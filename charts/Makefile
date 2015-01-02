# -*- encoding: utf-8 -*-

# These are some simple tests to ensure that the output of
# this converter matches the output of the original converter:

# If you have Oerp 7 installed, set the path to the addons and run
# make test-uk
# This will run the converter on the $OERP_7_ADDONS/l10n_uk/data directory
# to generate a Tryton CofAs into accounting_chart_uk_oerp7.xml
# This chart will be tested and later packaged into a trytond module.

# If you have Oerp 7.0 installed, set the following path to the addons
OERP_7_ADDONS="/n/src/openerp-7.0-20140125-002455/openerp/addons"
# If you have Oerp 6.0.4 installed, set the following path to the addons
OERP_6_ADDONS="/n/src/openerp-server-6.0.4/bin/addons"

test:: test-nl test-uk

test-nl:: test-nl-orig test-nl-new

# This tests the original converter and the original NL chart from
# https://github.com/pjstevns/trytond_account_nl
test-nl-orig::
	python ../converter-orig.py && \
		diff account_nl-orig.xml account_nl.xml

# This tests this converter and the original NL chart from
# https://github.com/pjstevns/trytond_account_nl
test-nl-new::
	python ../converter.py --lang=nl \
	  -o account_nl-new.xml \
	  account_chart_netherlands.xml && \
	diff account_nl-orig.xml account_nl-new.xml

test-uk:: test-uk-6 test-uk-7

OERP7_L10N_UK_DATA=${OERP_7_ADDONS}/"l10n_uk/data"
test-uk-7::
# only do this test if the directory exists
	[ ! -d ${OERP7_L10N_UK_DATA} ] || \
		$(MAKE) $(MFLAGS) accounting_chart_uk_oerp7.xml

# 990 accounts chart by smartmode.co.uk
oerp7_chart_l10n_uk.xml::
	${SHELL} openerp7-l10n_uk-csv-to-xml.sh ${OERP7_L10N_UK_DATA} > $@

accounting_chart_uk_oerp7.xml::  oerp7_chart_l10n_uk.xml
	python ../converter.py --lang=en \
	  $< > accounting_chart_uk_oerp7.xml

OERP6_L10N_UK=${OERP_6_ADDONS}/"l10n_uk"
test-uk-6::
# only do this test if the directory exists
	[ ! -d ${OERP6_L10N_UK} ] || \
		$(MAKE) $(MFLAGS) accounting_chart_uk_oerp6.xml

# 29 account chart by seathsolutions.com
oerp6_chart_l10n_uk.xml::
	echo '<?xml version="1.0" encoding="utf-8"?>' > $@
	echo '<openerp>' >> $@
	echo '    <data noupdate="True">' >> $@
	cat ${OERP6_L10N_UK}/l10n_uk_types.xml \
	    ${OERP6_L10N_UK}/l10n_uk_chart.xml \
	    ${OERP6_L10N_UK}/l10n_uk_tax.xml | \
		sed -e '/<\/*openerp/d' \
		    -e '/<\/*data/d' \
		    -e '/<\?xml/d' >> $@
	echo '    </data>' >> $@
	echo '</openerp>'>> $@

accounting_chart_uk_oerp6.xml::  oerp6_chart_l10n_uk.xml
	python ../converter.py --lang=en \
	    -c oerp6_chart_l10n_uk.cfg \
	  $< > accounting_chart_uk_oerp6.xml

clean::
	find . -type f -name \*~ -exec rm -f '{}' \;

veryclean:: clean
	rm -f account_nl-new.xml account_nl.xml
	rm -f accounting_chart_uk_oerp7.xml accounting_chart_uk_oerp6.xml
# leave the intermediaries for now for people who dont have them
#	rm -f oerp7_chart_l10n_uk.xml oerp6_chart_l10n_uk.xml 