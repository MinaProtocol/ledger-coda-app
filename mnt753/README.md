# Coda signature app for Ledger Blue & Ledger Nano S/X

Big disclaimer : This is a work in progress. Don't use it on a Ledger device
that is handling or has ever handled private keys associated with any accounts
of value.

This app grew loosely from the Ledger samplesign app, but all of the python in `/cli`
has been updated to use python3. So if you're here from another project and curious,
it seems it is possible!

Run `make` to check the build, and `make load` to build and load the application
onto the device. Errors try to be helpful and the most common reason for failure
is the device autolocking, so if something isn't working that might just be the
reason. `make delete` deletes the app.

See [Ledger's documentation](http://ledger.readthedocs.io) for further information.

To get the app version:
```
python3 cli/sign.py --request='version'
```
To generate and return the public key generated with nonce 11:
```
python3 cli/sign.py --request=publickey --nonce=11
```
To sign a transaction, with pk 1234 (`"nonce":37` in the JSON gives the signature/account nonce, `--nonce=1234` gives the nonce with which the Ledger device will generate the sender private/public keypair):
```
python3 cli/sign.py --request=transaction --nonce=1234 --transaction='{"sendPayment": {"is_delegation": "False","nonce": 37,"from": 123,"to": "tNci9iZe1p3KK4MCcqDa52mpxBTveEm3kqZMm7vwJF9uKzGGt1pCHVNa2oMevDb1HDAs4bNdMQLNbD8N3tkCtKNGM53obE9qFkkhmqMnKRLNLiSfPJuLGsSwqnL3HxSqciJoqJJJmq5Cfb","amount": 1000,"fee": 8,"valid_until": 1600,"memo": "2pmu64f2x97tNiDXMycnLwBSECDKbX77MTXVWVsG8hcRFsedhXDWWq"}}'
```

## mnt753
`mnt753` contains all the same directories as above, except implementing the
elliptic curve arithmetic over mnt753 instead of bn382. It also contains the
scripts needed to generate the binaries that are released so that users don't
have to install all the dependencies and compile everything themselves in
order to load and use the app on the Ledger devices.

## mnt753/ledger-precompile
`mnt753/ledger-precompile` includes scripts for loading and deleting the app,
with all of the SDK and C compiler requirements removed. `delete.sh` deletes
the app called 'Coda' on the user's Ledger device, and so nothing other than
python3 itself and the python3 ledgerblue library needs to be installed on a
user's machine to use this script. `load.sh` also has dependencies on python3
and the python3 ledgerblue library, and additionally expects there to be an
app file in `./bin/app.hex`. This is contained in the release
[here](https://github.com/CodaProtocol/ledger-coda-app/releases/tag/v0.1.0).

`load.sh` and `delete.sh` both contain variables called `TARGET_ID` and
`TARGET_VERSION`. `TARGET_ID="0x31100004"` means that the scripts are being
run for the Ledger Nano S, and `TARGET_VERSION="1.6.0"` means that they are
being run for firmware version `1.6.0`. Changing to other firmware versions
may not cause any issues, but it is currently untested. Changing to different
target IDs probably will cause issues, but this is also currently untested.
