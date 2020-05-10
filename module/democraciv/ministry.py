import typing
import discord

from util.flow import Flow
from util.converter import Bill
from config import config, links
from util.paginator import Pages
from discord.ext import commands
from discord.ext.commands import Greedy
from util.law_helper import MockContext, AnnouncementQueue
from util import mk, exceptions, utils


class LawPassScheduler(AnnouncementQueue):

    def get_message(self) -> str:
        message = [f"{mk.get_democraciv_role(self.bot, mk.DemocracivRole.GOVERNMENT_ROLE).mention}, "
                   f"the following bills were **passed into law by the Ministry**.\n"]

        for obj in self._objects:
            message.append(f"-  **{obj.name}** (<{obj.tiny_link}>)")

        message.append(f"\nAll new laws were added to `{config.BOT_PREFIX}laws` and can now be found with "
                       f"`{config.BOT_PREFIX}laws search <query>`. The "
                       f"{mk.get_democraciv_role(self.bot, mk.DemocracivRole.SPEAKER_ROLE).mention} should add them to "
                       f"the Legal Code as soon as possible.")
        return '\n'.join(message)


class LawVetoScheduler(AnnouncementQueue):

    def get_message(self) -> str:
        message = [f"{mk.get_democraciv_role(self.bot, mk.DemocracivRole.SPEAKER_ROLE).mention}, "
                   f"the following bills were **vetoed by the Ministry**.\n"]

        for obj in self._objects:
            message.append(f"-  **{obj.name}** (<{obj.tiny_link}>)")

        return '\n'.join(message)


class Ministry(commands.Cog):
    """Allows the Ministry to pass or veto bills from the Legislature."""

    def __init__(self, bot):
        self.bot = bot
        self.pass_scheduler = LawPassScheduler(bot, mk.DemocracivChannel.GOV_ANNOUNCEMENTS_CHANNEL)
        self.veto_scheduler = LawVetoScheduler(bot, mk.DemocracivChannel.GOV_ANNOUNCEMENTS_CHANNEL)

    @property
    def prime_minister(self) -> typing.Optional[discord.Member]:
        try:
            return mk.get_democraciv_role(self.bot, mk.DemocracivRole.PRIME_MINISTER_ROLE).members[0]
        except (IndexError, exceptions.RoleNotFoundError):
            return None

    @property
    def lt_prime_minister(self) -> typing.Optional[discord.Member]:
        try:
            return mk.get_democraciv_role(self.bot, mk.DemocracivRole.LT_PRIME_MINISTER_ROLE).members[0]
        except (IndexError, exceptions.RoleNotFoundError):
            return None

    @property
    def speaker(self) -> typing.Optional[discord.Member]:
        try:
            return mk.get_democraciv_role(self.bot, mk.DemocracivRole.SPEAKER_ROLE).members[0]
        except (IndexError, exceptions.RoleNotFoundError):
            return None

    @property
    def gov_announcements_channel(self) -> typing.Optional[discord.TextChannel]:
        return mk.get_democraciv_channel(self.bot, mk.DemocracivChannel.GOV_ANNOUNCEMENTS_CHANNEL)

    async def get_open_vetos(self) -> typing.List[Bill]:
        """Gets all bills that passed the Legislature, are vetoable and were not yet voted on by the Ministry"""
        open_bills = await self.bot.db.fetch('SELECT id FROM legislature_bills WHERE has_passed_leg = true'
                                             ' AND is_vetoable = true AND voted_on_by_ministry = false'
                                             ' AND has_passed_ministry = false ORDER BY id')

        return [await Bill.convert(MockContext(self.bot), record['id']) for record in open_bills]

    async def get_pretty_vetos(self) -> typing.Optional[typing.List[str]]:
        """Prettifies a list of Bill objects of open vetoes into list of strings"""
        open_bills = await self.get_open_vetos()

        pretty_bills = []

        if len(open_bills) > 0:
            for bill in open_bills:
                pretty_bills.append(f"Bill #{bill.id} - [{bill.name}]({bill.tiny_link})")

        if not pretty_bills:
            return None

        return pretty_bills

    @commands.group(name='ministry', aliases=['m', 'min'], case_insensitive=True, invoke_without_command=True)
    @commands.cooldown(1, config.BOT_COMMAND_COOLDOWN, commands.BucketType.user)
    async def ministry(self, ctx):
        """Dashboard for Ministers with important links and updates on new bills"""

        embed = self.bot.embeds.embed_builder(title=f"The Ministry of {mk.NATION_NAME}", description="")

        pretty_bills = await self.get_pretty_vetos()

        if pretty_bills is None:
            pretty_bills = 'There are no new bills to vote on.'
        else:
            pretty_bills = f"You can vote on new bills, check `{ctx.prefix}ministry bills`."

        minister_value = []

        if isinstance(self.prime_minister, discord.Member):
            minister_value.append(f"Prime Minister: {self.prime_minister.mention}")
        else:
            minister_value.append("Prime Minister: -")

        if isinstance(self.lt_prime_minister, discord.Member):
            minister_value.append(f"Lt. Prime Minister: {self.lt_prime_minister.mention}")
        else:
            minister_value.append("Lt. Prime Minister: -")

        embed.add_field(name="Head of State", value='\n'.join(minister_value))
        embed.add_field(name="Links", value=f"[Constitution]({links.constitution})\n"
                                            f"[Legal Code]({links.laws})\n"
                                            f"[Ministry Worksheet]({links.executiveworksheet})\n"
                                            f"[Ministry Procedures]({links.execprocedures})", inline=True)
        embed.add_field(name="Open Bills", value=pretty_bills, inline=False)
        await ctx.send(embed=embed)

    @ministry.command(name='bills', aliases=['b'])
    @commands.cooldown(1, config.BOT_COMMAND_COOLDOWN, commands.BucketType.user)
    async def bills(self, ctx):
        """See all open bills from the Legislature to vote on"""

        pretty_bills = await self.get_pretty_vetos()

        if pretty_bills is None:
            embed = self.bot.embeds.embed_builder(title="There are no new bills to vote on.",
                                                  description="",
                                                  has_footer=False)
            return await ctx.send(embed=embed)

        help_description = f"Use '{config.BOT_PREFIX}help ministry' to learn how to pass and veto bills."

        pages = Pages(ctx=ctx, entries=pretty_bills, show_entry_count=False, title="Open Bills to Vote On",
                      show_index=False, footer_text=help_description, show_amount_of_pages=True)
        if pages.maximum_pages == 1:
            pages.show_amount_of_pages = False
        await pages.paginate()

    @staticmethod
    async def verify_bill(bill: Bill) -> str:
        if not bill.is_vetoable:
            return "The Ministry cannot veto this!"

        if not bill.passed_leg:
            return "This bill hasn't passed the Legislature yet!"

        if bill.voted_on_by_ministry:
            return "You already voted on this bill!"

    @ministry.command(name='veto', aliases=['v'])
    @commands.cooldown(1, config.BOT_COMMAND_COOLDOWN, commands.BucketType.user)
    @utils.has_any_democraciv_role(mk.DemocracivRole.PRIME_MINISTER_ROLE, mk.DemocracivRole.LT_PRIME_MINISTER_ROLE)
    async def veto(self, ctx, bill_ids: Greedy[Bill]):
        """Veto one or multiple bills

        **Example:**
            `-ministry veto 12` will veto Bill #12
            `-ministry veto 45 46 49 51 52` will veto all those bills"""

        if not bill_ids:
            return await ctx.send_help(ctx.command)

        bills = bill_ids
        flow = Flow(self.bot, ctx)

        error_messages = []

        for _bill in bills:
            error = await self.verify_bill(_bill)
            if error:
                error_messages.append((_bill, error))

        if error_messages:
            # Remove bills that did not pass verify_bill from bills list
            bills[:] = [b for b in bills if b not in list(map(list, zip(*error_messages)))[0]]

            error_messages = '\n'.join(
                [f"-  **{_bill.name}** (#{_bill.id}): _{reason}_" for _bill, reason in error_messages])
            await ctx.send(f":warning: The following bills can not be vetoed.\n{error_messages}")

        # If all bills failed verify_bills, return
        if not bills:
            return

        pretty_bills = '\n'.join([f"-  **{_bill.name}** (#{_bill.id})" for _bill in bills])
        are_you_sure = await ctx.send(f":information_source: Are you sure that you want"
                                      f" to veto the following bills?"
                                      f"\n{pretty_bills}")

        reaction = await flow.get_yes_no_reaction_confirm(are_you_sure, 200)

        if reaction is None:
            return

        if not reaction:
            return await ctx.send("Aborted.")

        elif reaction:
            async with ctx.typing():
                for _bill in bills:
                    await _bill.veto()
                    self.veto_scheduler.add(_bill)

                await ctx.send(":white_check_mark: All bills were vetoed.")

    @ministry.command(name='pass', aliases=['p'])
    @commands.cooldown(1, config.BOT_COMMAND_COOLDOWN, commands.BucketType.user)
    @utils.has_any_democraciv_role(mk.DemocracivRole.PRIME_MINISTER_ROLE, mk.DemocracivRole.LT_PRIME_MINISTER_ROLE)
    async def pass_bill(self, ctx, bill_ids: Greedy[Bill]):
        """Pass one or multiple bills into law

        **Example:**
            `-ministry pass 12` will pass Bill #12 into law
            `-ministry pass 45 46 49 51 52` will pass all those bills into law"""

        bills = bill_ids
        flow = Flow(self.bot, ctx)

        error_messages = []

        for bill in bills:
            error = await self.verify_bill(bill)
            if error:
                error_messages.append((bill, error))

        if error_messages:
            # Remove bills that did not pass verify_bill from bills list
            bills = [b for b in bills if b not in list(map(list, zip(*error_messages)))[0]]

            error_messages = '\n'.join(
                [f"-  **{_bill.name}** (#{_bill.id}): _{reason}_" for _bill, reason in error_messages])
            await ctx.send(f":warning: The following bills can not be passed into law.\n{error_messages}")

        # If all bills failed verify_bills, return
        if not bills:
            return

        pretty_bills = '\n'.join([f"-  **{_bill.name}** (#{_bill.id})" for _bill in bills])
        are_you_sure = await ctx.send(f":information_source: Are you sure that you want "
                                      f"to pass the following bills into law?"
                                      f"\n{pretty_bills}")

        reaction = await flow.get_yes_no_reaction_confirm(are_you_sure, 200)

        if reaction is None:
            return

        if not reaction:
            return await ctx.send("Aborted.")

        elif reaction:
            async with ctx.typing():
                for bill in bills:
                    await bill.pass_into_law()
                    self.pass_scheduler.add(bill)

                await ctx.send(":white_check_mark: All bills were passed into law.")


def setup(bot):
    bot.add_cog(Ministry(bot))
