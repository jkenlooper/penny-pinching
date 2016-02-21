# Penny Pinching

Manage finances through a web interface.  It is kinda like a 'envelope
budgeting' system where money is set aside for different expense categories.

## Install

The development version can be installed with pip in editable mode:

    pip install -e .

That will create a `pennypinching` command.  To get the rest setup you will
need to copy and edit the example config files:

    cp app-example.conf app.conf;
    cp users-example.yaml users.yaml;
    # Edit the app.conf and users.yaml with a text editor.
    # Create the 'db_directory' that app.conf refers to.

Start the app by running `pennypinching 8080 run` in a terminal.  Visit the url
http://localhost:8080/ in a web browser.  The page will show a list of
databases based on your users.yaml.  Clicking on one will show the transactions
page for it.

## Usage and stuff

Well, uhm, good luck.  I wrote this for my own purposes years ago and have used
it off and on since.  I haven't bothered writing any documentation on how to
use the application.  Think of it as a fun puzzle to solve and you'll be fine.
