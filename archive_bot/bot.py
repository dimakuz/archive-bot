import dataclasses
import logging
import os
import pathlib
import typing

import pikepdf
import telegram as tg
import telegram.ext


@dataclasses.dataclass
class Config:
    token: str
    dest_dir: str
    allowed_users: typing.Iterable[str]
    passwords: typing.Dict[str, str]

    @classmethod
    def from_env(cls):
        allowed_users = []
        if os.getenv('ALLOWED_USERS') is not None:
            allowed_users.extend(os.getenv('ALLOWED_USERS').split(','))

        passwords = {}
        if os.getenv('PDF_PASSWORDS') is not None:
            for entry in os.getenv('PDF_PASSWORDS').split(','):
                name, val = entry.split(':', maxsplit=1)
                passwords[name] = val
        return cls(
            token=os.getenv('TOKEN'),
            dest_dir=os.getenv('DEST_DIR'),
            allowed_users=allowed_users,
            passwords=passwords,
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

        if not self._process_pdf(update, temp_path):
            return

        os.rename(temp_path, final_path)
        update.message.reply_text(
            f'{filename} stored successfully.'
        )

    def _temp_path(self, filename: str) -> str:
        return f'{self._config.dest_dir}/._{filename}'

    def _final_path(self, filename: str) -> str:
        return f'{self._config.dest_dir}/{filename}'

    def _process_pdf(self, update, path):
        if not _is_password_protected(path):
            return True

        for name, password in self._config.passwords.items():
            try:
                with pikepdf.open(path, password=password) as f:
                    f.save(f'{path}.out')
                    os.rename(f'{path}.out', path)
                    update.message.reply_text(
                        f'Decrypted with {name} password',
                    )
                    return True
            except pikepdf._qpdf.PasswordError:
                continue
        update.message.reply_text('PDF is encrypted with unknown password')
        return False


def _is_password_protected(path):
    try:
        with pikepdf.open(path):
            return False
    except pikepdf._qpdf.PasswordError:
        return True


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
