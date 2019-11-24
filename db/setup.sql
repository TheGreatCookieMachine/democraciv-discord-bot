CREATE TABLE IF NOT EXISTS guilds(
    id bigint PRIMARY KEY,
    welcome bool,
    welcome_message text,
    welcome_channel bigint,
    logging bool,
    logging_channel bigint,
    logging_excluded bigint[],
    defaultrole bool,
    defaultrole_role bigint

);

CREATE TABLE IF NOT EXISTS roles(
    guild_id bigint references guilds(id),
    role text,
    join_message text
);




