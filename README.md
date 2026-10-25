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

1. Install **Python 3.10 or newer**.
2. Open [Thrum on GitHub](https://github.com/SiliconScientist/thrum), select
   **Code**, then **Download ZIP**, and save it in your Downloads folder.
3. Extract the ZIP. On macOS, double-click it; on Windows, right-click it and
   select **Extract All**. This creates a project folder, usually `thrum-main`,
   containing this `README.md` and the `thrum/` directory. No Git installation
   or GitHub account is needed for a public repository download.

### Try the fictional demo

Explore a fictional neighborhood repair café: meet its volunteers, find their
skills, and follow connections between a workshop, library, and community group.
Open a terminal and run the
following on macOS or Linux. Adjust the `cd` path
if you extracted the project elsewhere or its folder has a different name:

```sh
cd ~/Downloads/thrum-main
python3 -m thrum --db ~/.local/share/thrum-demo/people.sqlite init
python3 -m thrum --db ~/.local/share/thrum-demo/people.sqlite demo
python3 -m thrum --db ~/.local/share/thrum-demo/people.sqlite serve
```

Open the URL printed in your terminal to explore (usually **http://127.0.0.1:8765/**).
If that port is busy, Thrum automatically uses a free port. Stop with **Ctrl-C**.
Next time, return to the same project folder and run only the last command.
See the [demo walkthrough](docs/USAGE.md#explore-the-repair-café) for things to try.

### Add your own contacts

Stop the demo with **Ctrl-C**, then run these commands from the same project
folder to start your own database, kept separate from the fictional contacts:

```sh
python3 -m thrum init
python3 -m thrum serve
```

Open the URL printed in your terminal and select **Add contact**.
Stop with **Ctrl-C**; next time, return to the same project folder and run
`python3 -m thrum serve`.

If you see `No module named thrum`, check your current folder: these commands
run from the project folder, not its parent (such as `~/Downloads`) or the
inner `thrum/` directory. No package installation is required.

See the [user guide](docs/USAGE.md) for more help and Windows notes.

## Learn more

- [Using Thrum](docs/USAGE.md): contacts, relationships, backups, exports, and restores.
- [Privacy and security](docs/PRIVACY.md): safeguards and limitations.
- [Development](docs/DEVELOPMENT.md): architecture, customization, testing, and dependencies.
- [Audit report](docs/AUDIT.md): implementation review and validation results.

Open source under the [MIT License](LICENSE).
