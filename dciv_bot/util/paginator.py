"""
The MIT License (MIT)

Copyright (c) 2015 Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import asyncio
import discord

from discord.embeds import EmptyEmbed
from dciv_bot.config import config
from discord.ext.commands import Paginator as CommandPaginator


class CannotPaginate(Exception):
    pass


class Pages:
    """Implements a paginator that queries the user for the
    pagination interface.
    Pages are 1-index based, not 0-index based.
    If the user does not reply within 2 minutes then the pagination
    interface exits automatically.
    Parameters
    ------------
    ctx: Context
        The context of the command.
    entries: List[str]
        A list of entries to paginate.
    per_page: int
        How many entries show up per page.
    show_entry_count: bool
        Whether to show an entry count in the footer.
    Attributes
    -----------
    embed: discord.Embed
        The embed object that is being used to send pagination info.
        Feel free to modify this externally. Only the description,
        footer fields, and colour are internally modified.
    permissions: discord.Permissions
        Our permissions for the channel.
    """

    def __init__(self, ctx, *, entries, per_page=12, show_entry_count=True, title=None, show_index=True,
                 footer_text=config.BOT_NAME, colour=config.BOT_EMBED_COLOUR, title_url=None, thumbnail=None,
                 show_amount_of_pages=False, author_icon=EmptyEmbed):
        self.bot = ctx.bot
        self.entries = entries
        self.message = ctx.message
        self.channel = ctx.channel
        self.author = ctx.author
        self.per_page = per_page
        self.show_index = show_index
        self.footer = footer_text
        self.title = title
        self.icon = author_icon
        self.embed = discord.Embed(colour=colour)

        pages, left_over = divmod(len(self.entries), self.per_page)
        if left_over:
            pages += 1

        self.maximum_pages = pages

        if title_url:
            self.embed.url = title_url
        if thumbnail:
            self.embed.set_thumbnail(url=thumbnail)

        self.paginating = len(entries) > per_page
        self.show_entry_count = show_entry_count
        self.show_amount_of_pages = show_amount_of_pages

        # This often leads to weird ratelimit situations, thus we remove the stop and info buttons as they are
        # rarely used anyway.
        self.reaction_emojis = [
            (config.HELP_FIRST, self.first_page),
            (config.HELP_PREVIOUS, self.previous_page),
            (config.HELP_NEXT, self.next_page),
            (config.HELP_LAST, self.last_page),
            # ('\N{BLACK SQUARE FOR STOP}', self.stop_pages)
            # ('\N{INFORMATION SOURCE}', self.show_help),
        ]

        if ctx.guild is not None:
            self.permissions = self.channel.permissions_for(ctx.guild.me)
        else:
            self.permissions = self.channel.permissions_for(ctx.bot.user)

        if not self.permissions.embed_links:
            raise CannotPaginate(':x: Bot does not have embed links permission.')

        if not self.permissions.send_messages:
            raise CannotPaginate(':x: Bot cannot send messages.')

        if self.paginating:
            # verify we can actually use the pagination session
            if not self.permissions.add_reactions:
                raise CannotPaginate(':x: Bot does not have add reactions permission.')

            if not self.permissions.read_message_history:
                raise CannotPaginate(':x: Bot does not have Read Message History permission.')

    def get_page(self, page):
        base = (page - 1) * self.per_page
        return self.entries[base:base + self.per_page]

    def get_content(self, entries, page, *, first=False):
        return None

    def get_embed(self, entries, page, *, first=False):
        self.prepare_embed(entries, page, first=first)
        return self.embed

    def prepare_embed(self, entries, page, *, first=False):
        p = []
        for index, entry in enumerate(entries, 1 + ((page - 1) * self.per_page)):
            if self.show_index:
                p.append(f'{index}. {entry}')
            else:
                p.append(f'{entry}')

        if self.maximum_pages > 1:
            if self.show_entry_count:
                text = f'Page {page}/{self.maximum_pages} ({len(self.entries)} entries)'
            else:
                text = f'Page {page}/{self.maximum_pages}'

        self.embed.title = self.title
        self.embed.description = '\n'.join(p)
        self.embed.set_footer(text=self.footer, icon_url=config.BOT_ICON_URL)

        if self.maximum_pages:
            if self.show_amount_of_pages:
                self.embed.set_author(icon_url=self.icon, name=f'Page {page}/{self.maximum_pages}')

    async def show_page(self, page, *, first=False):
        self.current_page = page
        entries = self.get_page(page)
        content = self.get_content(entries, page, first=first)
        embed = self.get_embed(entries, page, first=first)

        if not self.paginating:
            return await self.channel.send(content=content, embed=embed)

        if not first:
            await self.message.edit(content=content, embed=embed)
            return

        self.message = await self.channel.send(content=content, embed=embed)
        for (reaction, _) in self.reaction_emojis:
            if self.maximum_pages == 2 and reaction in ('\u23ed', '\u23ee'):
                # no |<< or >>| buttons if we only have two pages
                # we can't forbid it if someone ends up using it but remove
                # it from the default set
                continue

            await self.message.add_reaction(reaction)

    async def checked_show_page(self, page):
        if page != 0 and page <= self.maximum_pages:
            await self.show_page(page)

    async def first_page(self):
        """goes to the first page"""
        await self.show_page(1)

    async def last_page(self):
        """goes to the last page"""
        await self.show_page(self.maximum_pages)

    async def next_page(self):
        """goes to the next page"""
        await self.checked_show_page(self.current_page + 1)

    async def previous_page(self):
        """goes to the previous page"""
        if self.current_page == 0:
            return

        await self.checked_show_page(self.current_page - 1)

    async def show_current_page(self):
        if self.paginating:
            await self.show_page(self.current_page)

    async def show_help(self):
        """shows this message"""
        messages = ['Welcome to the interactive paginator!\n',
                    'This interactively allows you to see pages of text by navigating with '
                    'reactions. They are as follows:\n']

        for (emoji, func) in self.reaction_emojis:
            messages.append(f'{emoji} {func.__doc__}')

        embed = self.embed.copy()
        embed.clear_fields()
        embed.description = '\n'.join(messages)
        embed.set_footer(text=f'We were on page {self.current_page} before this message.')
        await self.message.edit(content=None, embed=embed)

        async def go_back_to_current_page():
            await asyncio.sleep(60.0)
            await self.show_current_page()

        self.bot.loop.create_task(go_back_to_current_page())

    async def stop_pages(self):
        """stops the interactive pagination session"""
        await self.message.delete()
        self.paginating = False

    def react_check(self, payload):
        if payload.user_id != self.author.id:
            return False

        if payload.message_id != self.message.id:
            return False

        to_check = str(payload.emoji)
        for (emoji, func) in self.reaction_emojis:
            if to_check == emoji:
                self.match = func
                return True
        return False

    async def paginate(self):
        """Actually paginate the entries and run the interactive loop if necessary."""
        first_page = self.show_page(1, first=True)
        if not self.paginating:
            await first_page
        else:
            # allow us to react to reactions right away if we're paginating
            self.bot.loop.create_task(first_page)

        while self.paginating:
            try:
                payload = await self.bot.wait_for('raw_reaction_add', check=self.react_check, timeout=120.0)
            except asyncio.TimeoutError:
                self.paginating = False
                try:
                    await self.message.clear_reactions()
                except:
                    pass
                finally:
                    break

            try:
                await self.message.remove_reaction(payload.emoji, discord.Object(id=payload.user_id))
            except:
                pass  # can't remove it so don't bother doing so

            await self.match()


class AlternativePages(Pages):

    def __init__(self, *args, **kwargs):
        self.a_title = kwargs.pop('a_title', "")
        self.a_icon = kwargs.pop('a_icon', EmptyEmbed)
        self.a_thumbnail = kwargs.pop('a_thumbnail', EmptyEmbed)
        super().__init__(*args, **kwargs)

    def prepare_embed(self, entries, page, *, first=False):
        super().prepare_embed(entries, page, first=first)

        if self.a_thumbnail:
            self.embed.set_thumbnail(url=self.a_thumbnail)

        if self.maximum_pages > 1 and self.show_amount_of_pages:
            self.embed.set_footer(text=f'Page {page}/{self.maximum_pages}')
        else:
            self.embed.set_footer(text=EmptyEmbed, icon_url=EmptyEmbed)

        self.embed.set_author(icon_url=self.a_icon, name=self.a_title)


class FieldPages(Pages):
    """Similar to Pages except entries should be a list of
    tuples having (key, value) to show as embed fields instead.
    """

    def prepare_embed(self, entries, page, *, first=False):
        self.embed.clear_fields()
        self.embed.description = discord.Embed.Empty

        for key, value in entries:
            self.embed.add_field(name=key, value=value, inline=False)

        if self.maximum_pages > 1:
            if self.show_entry_count:
                text = f'Page {page}/{self.maximum_pages} ({len(self.entries)} entries)'
            else:
                text = f'Page {page}/{self.maximum_pages}'

            self.embed.set_footer(text=text)


class TextPages(Pages):
    """Uses a commands.Paginator internally to paginate some text."""

    def __init__(self, ctx, text, *, prefix='```', suffix='```', max_size=2000):
        paginator = CommandPaginator(prefix=prefix, suffix=suffix, max_size=max_size - 200)
        for line in text.split('\n'):
            paginator.add_line(line)

        super().__init__(ctx, entries=paginator.pages, per_page=1, show_entry_count=False)

    def get_page(self, page):
        return self.entries[page - 1]

    def get_embed(self, entries, page, *, first=False):
        return None

    def get_content(self, entry, page, *, first=False):
        if self.maximum_pages > 1:
            return f'{entry}\nPage {page}/{self.maximum_pages}'
        return entry
