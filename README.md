# Coda signature app for Ledger Blue & Ledger Nano S/X

Big disclaimer : This is a work in progress. Don't use it on a Ledger device
that is handling or has ever handled private keys associated with any accounts
of value.

Run `make` to check the build, and `make load` to build and load the application
onto the device. Errors try to be helpful and the most common reason for failure
is the device being locked, so if something isn't working, that could be the
reason. `make delete` deletes the app.

See [Ledger's documentation](http://ledger.readthedocs.io) for further information.

Generally you won't have to run these commands yourself as the codaledgercli library
will be installed, but without installing the library, to get the app version, you run:
```
python3 codaledgercli/__main__.py --request='version'
```
To generate and return the public key generated with `HDindex` 11:
```
python3 codaledgercli/__main__.py --request=publickey --HDindex=11
```
All of the information for a transaction is contained in two field elements. These
are produced by the Coda client. To sign a transaction, the command is then:
```
python3 codaledgercli/__main__.py --request=transaction --HDindex=1234 --msgx=recipientpkx --msgm=allotherinfo
```
