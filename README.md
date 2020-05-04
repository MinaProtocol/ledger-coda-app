# Coda signature app for Ledger Blue & Ledger Nano S/X

Big disclaimer : This is a work in progress. Don't use it on a Ledger device
that is handling or has ever handled private keys associated with any accounts
of value.

Run `make` to check the build, and `make load` to build and load the
application onto the device. Errors try to be helpful and the most common
reason for failure is the device being locked, so if something isn't working,
that could be the reason. `make delete` deletes the app.

See [Ledger's documentation](http://ledger.readthedocs.io) for further
information.

Generally you won't have to run these commands yourself as the codaledgercli
library will be installed, but without installing the library, to get the app
version, you run: ``` python3 codaledgercli/__main__.py --request='version' ```
To generate and return the public key generated with `HDindex` 11: ``` python3
codaledgercli/__main__.py --request=publickey --HDindex=11 ``` All of the
information for a transaction is contained in two field elements. These are
produced by the Coda client. To sign a transaction, the command is then: ```
python3 codaledgercli/__main__.py --request=transaction --HDindex=1234
--msgx=recipientpkx --msgm=allotherinfo ```

## Developing

### codaledgercli

`codaledgercli` contains the python code that acts as a bridge between the
computer and the Ledger device.  This means it's also used so that the Coda
client and Ledger app can interact. The code in `codaledgercli` is distributed
as a library (this happens by running some commands with `setup.py`), and it is
needed to:
- load and delete the Ledger app on the Ledger device (in the future, the app
  should be listed on [Ledger Live](https://www.ledger.com/ledger-live) and so
  that can be used to distribute, load, delete, and interact with the Ledger
  app).
- interact with the Ledger app. The current functionality consists of sending
  commands to the Ledger app to:
  - get the app version (taking no additional parameters),
  - generate a keypair from an `HDindex` (an integer), which results in the
    public key being sent back to the computer,
  - generate a signature from a message to be signed, and an `HDindex` with
    which to generate the keypair used for signing.  The python code just acts
    as a bridge, and the actual Ledger app code is written in C, and found in
    `src`.

### test

`test` contains python scripts useful when testing new functionality on the
Ledger device. In includes python implementations of elliptic curve arithmetic,
poseidon, and signing, so you can make sure hashing is consistent on and
off-device, and that signatures generating on device verify as expected.

### src

`src` contains the code that is loaded onto the Ledger device. The loading
itself makes use of the python contained the `ledgerblue` library. This code is
loaded using `Makefile` and depends on the Ledger dev SDK.  Instructions on how
to load this code onto your Ledger device are
[here](https://github.com/CodaProtocol/coda/blob/develop/frontend/website/pages/docs/hardware-wallet.mdx).
The comments in files inside `src` explain more thoroughly what they do, but in
brief, it contains all of the code for the app to function, including elliptic
curve cryptography, the poseidon hash function, and signature generation.  The
files in `glyphs` are used by the code in `src`, as is `nanos_app_coda.gif`.
