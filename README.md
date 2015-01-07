trytond_chart_converter
=======================

Convert OpenERP chart of accounts to Tryton
This is a converter to convert OpenERP chart of accounts in XML
to Tryton's format based on the converter by Paul J. Stevens:
http://github.com/pjstevns/trytond_account_nl/

**THIS IS A WORK IN PROGRESS, UNRELEASED FOR NOW!**

HomePage: 

Ideally, the converter could be internationalized the way Tryton
modules are, but to start with, there is a simple `--lang`
command-line switch and an array of strings for each language.
I've started moving some of this information to a config file,
and I think that there's more Oerp dependencies to be pulled out.
Only the original 'nl' and the new 'en' langs are available for now.

I like the idea of converting from OpenERP charts, because some
of the OpenERP charts keep improving as errors are detected or
accounting laws change, so it's nice not to have to redo this
accounting work in Tryton. And of course, it will help some
OpenERP->Tryton migrations where people have customized CoAs.
( If you haven't already seen this, it will make you smile:
https://www.openlabs.co.in/article/erp-trade-in-offer )

The original converter is the file `converter-orig.py`
(current from github as of 2014-12) and
the original input: `charts/account_chart_netherlands.xml`
and the original output: `account_nl-orig.xml`

There is no setup.py or installation, just the single script:
```
    python converter.py --help
```    

Every input chart can have a config file to parameterize the
conversion process. See `en.cfg` and `nl.cfg` for examples.

There are some simple tests to ensure that the output of
this converter matches the output of the original converter:
```
    make test
```
If you have Oerp 7.0 installed, set the path to the addons
as `OERP_7_ADDONS` in `charts/Makefile`, and if you have Oerp 6.0.4 installed,
set the path to the addons as `OERP_6_ADDONS` in charts/Makefile.
This will run the converter on the `$OERP_7_ADDONS/l10n_uk/data` directory
to generate a Tryton CofAs in `accounting_chart_uk_oerp7.xml`
and `accounting_chart_uk_oerp6.xml`.


**Usage: **
```
usage: converter.py [options] INPUTFILE

Options:
  -h, --help            show this help message and exit
  -o SOUTFILE, --outfile=SOUTFILE
                        the Tryton output XML file to convert to
  -c SCONFIGFILE, --config=SCONFIGFILE
                        the config file to govern the conversion (defaults to
                        <lang>.cfg)
  -l SLANG, --lang=SLANG
                        the language code to use: one of [en,nl]
  -t, --test            run the doctests in this file
```
