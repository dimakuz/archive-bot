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


class Bot:
    def __init__(self, config):
        self._config = config

    def run(self):
        updater = tg.ext.Updater(self._config.token)
        dispatcher = updater.dispatcher
        user_filter = telegram.ext.Filters.user()
        user_filter.add_usernames(self._config.allowed_users)

        dispatcher.add_handler(
            tg.ext.MessageHandler(
                user_filter & tg.ext.Filters.document.pdf,
                self._store_document,
            )
        )

        dispatcher.add_handler(
            tg.ext.MessageHandler(
                user_filter & tg.ext.Filters.all,
                self._ignore,
            ),
        )

        updater.start_polling()
        updater.idle()

    def _ignore(self, update: tg.Update, _: tg.ext.CallbackContext) -> None:
        update.message.reply_text('Ignoring...')

    def _store_document(
        self,
        update: tg.Update,
        _: tg.ext.CallbackContext
    ) -> None:
        filename = update.message.document.file_name
        temp_path = self._temp_path(filename)
        update.message.document.get_file().download(temp_path)

        final_path = self._final_path(filename)
        os.rename(temp_path, final_path)
        update.message.reply_text(
            f'{filename} stored successfully.'
        )

    def _temp_path(self, filename):
        return f'{self._config.dest_dir}/._{filename}'

    def _final_path(self, filename):
        return f'{self._config.dest_dir}/{filename}'


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

    bot = Bot(config)
    bot.run()


if __name__ == '__main__':
    main()
