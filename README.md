# Thrum

Thrum is a private, local-first relationship manager for remembering the people
and communities in your life. Keep contact details together, save the context
that matters, and see how people and organizations connect—all in a browser
on your own computer.

- **Remember the details:** names, affiliations, contact methods, tags, and notes.
- **See the connections:** record who introduced whom, who works together, and
  which organizations people belong to.
- **Find someone quickly:** search your contacts and filter by type or tag.
- **Keep control:** export your information and make local backups whenever you want.

## Why privacy matters

> Arguing that you don't care about the right to privacy because you have nothing
> to hide is no different than saying you don't care about free speech because
> you have nothing to say.
>
> — Edward Snowden, [Reddit AMA, May 21, 2015](https://www.reddit.com/r/IAmA/comments/36ru89/comment/crglgh2/)

Privacy gives us room to think, speak, and build relationships on our own terms.
A contact list holds more than addresses: it records friendships, communities,
and the trust other people place in us. Keeping that information private
respects their lives as well as our own.

Thrum keeps your data on your computer. There is no cloud account, telemetry,
or third-party service receiving your contacts. It works offline, its source
is open to inspection, and you can take your data with you. You decide what to
record, what to keep, and what to share.

Read about the [privacy protections and their limits](docs/PRIVACY.md).

## Quickstart

Install **Python 3.10 or newer**, download Thrum, and open a terminal in its folder.
On macOS or Linux, run:

```sh
python3 -m thrum init
python3 -m thrum serve
```

Open **http://127.0.0.1:8765/** and select **Add contact**.
Stop with **Ctrl-C**; next time, run just `python3 -m thrum serve`.

Prefer to explore first? [Try the fictional demo](docs/USAGE.md#try-thrum).
See the [user guide](docs/USAGE.md) for more help and Windows notes.

## Learn more

- [Using Thrum](docs/USAGE.md): contacts, relationships, backups, exports, and restores.
- [Privacy and security](docs/PRIVACY.md): safeguards and limitations.
- [Development](docs/DEVELOPMENT.md): architecture, customization, testing, and dependencies.
- [Audit report](docs/AUDIT.md): implementation review and validation results.

Open source under the [MIT License](LICENSE).
