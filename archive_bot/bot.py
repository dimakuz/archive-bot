import dataclasses
import logging
import os
import pathlib
import typing

import telegram as tg
import telegram.ext


@dataclasses.dataclass
class Config:
    token: str
    dest_dir: str
    allowed_users: typing.Iterable[str]

    @classmethod
    def from_env(cls):
        allowed_users = []
        if os.getenv('ALLOWED_USERS') is not None:
            allowed_users.extend(os.getenv('ALLOWED_USERS').split(','))
        return cls(
            token=os.getenv('TOKEN'),
            dest_dir=os.getenv('DEST_DIR'),
            allowed_users=allowed_users,
        )


def main() -> None:
    config = Config.from_env()

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG
    )

    if not config.token:
        raise RuntimeError('No token provided (TOKEN)')

    if not config.dest_dir:
        raise RuntimeError('No destination directory provided (DEST_DIR)')

    if not config.allowed_users:
        raise RuntimeError('No users specified (ALLOWED_USERS)')

    # Ensure target dir exists
    pathlib.Path(config.dest_dir).mkdir(exist_ok=True)

    updater = tg.ext.Updater(config.token)
    dispatcher = updater.dispatcher

    user_filter = telegram.ext.Filters.user()
    user_filter.add_usernames(config.allowed_users)

    def store_document(update: tg.Update, _: tg.ext.CallbackContext) -> None:
        update.message.document.get_file().download(
            f'{config.dest_dir}/._{update.message.document.file_name}',
        )
        os.rename(
            f'{config.dest_dir}/._{update.message.document.file_name}',
            f'{config.dest_dir}/{update.message.document.file_name}'
        )
        update.message.reply_text(
            f'{update.message.document.file_name} stored successfully.'
        )

    dispatcher.add_handler(
        tg.ext.MessageHandler(
            user_filter & tg.ext.Filters.document.pdf,
            store_document,
        )
    )

    def ignore(update: tg.Update, _: tg.ext.CallbackContext) -> None:
        update.message.reply_text('Ignoring...')

    dispatcher.add_handler(
        tg.ext.MessageHandler(
            user_filter & tg.ext.Filters.all,
            ignore,
        ),
    )

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
