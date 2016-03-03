#!/bin/sh
# -*- encoding: utf-8 -*-
__doc__="""
This is a simple script to convert the csv files in the data/ 
directory of the addons/l10n_uk module of OpenERP from
http://distfiles.gentoo.org/distfiles/openerp-7.0-20140125-002455.tar.gz
by http://www.smartmode.co.uk to XML.

The script is specfic to those csv files, but could be hacked to work
on other csv CofAs, or improved up to read the first line and use the
information there.

To run this script, execute it in this directory,
and provide the path to the data/ directory as an argument.

Capture the output to a file like oerp7_chart_l10_uk.xml
Loading the XML in Oerp7 should be equivalent to loading the CSV files, 
but YMMV.

USAGE: $0 /path/to/l10_uk/data
"""

if [ "$#" -ne 1 ] ; then
    echo $__doc__
    exit 1
  fi
if [ ! -d "$1" ] ; then
    echo "ERROR: directory not found: $1"
    exit 2
fi
DIR="$1"

IFS=,
cat << EOF
<?xml version="1.0" encoding="utf-8"?>
<openerp>
    <data noupdate="True">
EOF

# account.account.type
cat << EOF

        <!-- account.account.type -->
EOF
# "id","name","code","report_type","close_method"
grep '^"account' "$DIR/account.account.type.csv" | \
  dos2unix | \
  sed -f commas_in_csv.sed | \
  while read id name code report_type close_method ; do
cat << EOF
        <record model="account.account.type" id="$id" >
                <field name="name">$name</field>
                <field name="code">$code</field>
                <!-- <field name="report_type">$report_type</field> -->
                <field name="close_method">$close_method</field>
        </record>
EOF
  done

cat << EOF
        <!-- Chart template of l10n_uk -->
EOF
# Im not sure why I had this - remove it for now
cat > /dev/null << EOF
        <record id="a_root" model="account.account.template">
            <field name="name">UK Company Chart of Accounts</field>
            <field name="code">0</field>
            <field name="type">view</field>
            <field name="user_type" ref="account_type_view"/>
        </record>
EOF
cat << EOF
	<!-- account.account.template -->
EOF

# account.account.template
grep -v '^"id' "$DIR/account.account.template.csv" | \
  dos2unix | \
  sed -f commas_in_csv.sed | \
  while read id code name parent_id type user_type reconcile ; do
cat << EOF
        <record id="$id" model="account.account.template">
            <field name="name">$name</field>
            <field name="code">$code</field>
            <field name="type">$type</field>
            <field name="user_type" ref="$user_type"/>
            <field name="parent_id" ref="$parent_id"/>
EOF
if [ "$type" != 'view' ] ; then
    [ $reconcile == 'FALSE' ] && reconcile='False' || reconcile='True'
cat << EOF
            <field name="reconcile" eval="$reconcile"/>
EOF
    fi
cat << EOF
        </record>
EOF
  done

# account.chart.template.csv
cat << EOF

        <!-- account.chart.template.csv -->
EOF
# id,name,account_root_id:id,tax_code_root_id:id,bank_account_view_id:id,property_account_receivable:id,property_account_payable:id,property_account_expense_categ:id,property_account_income_categ:id,property_reserve_and_surplus_account:id
grep -v '^"id' "$DIR/account.chart.template.csv" | \
  dos2unix | \
  sed -f commas_in_csv.sed | \
  while read id name account_root_id tax_code_root_id bank_account_view_id property_account_receivable property_account_payable property_account_expense_categ property_account_income_categ property_reserve_and_surplus_account ; do
cat << EOF
        <record id="$id" model="account.chart.template">
            <field name="name">$name</field>
            <field name="account_root_id" ref="$account_root_id"/>
            <field name="tax_code_root_id" ref="$tax_code_root_id"/>
            <field name="bank_account_view_id" ref="$bank_account_view_id"/>
            <field name="property_account_receivable" ref="$property_account_receivable"/>     
            <field name="property_account_payable" ref="$property_account_payable"/>
            <field name="property_account_expense_categ" ref="$property_account_expense_categ"/>
            <field name="property_account_income_categ" ref="$property_account_income_categ"/>   
	    <field name="property_reserve_and_surplus_account" ref="$property_reserve_and_surplus_account"/>
        </record>
EOF
done

# account.tax.code.template.csv
cat << EOF

        <!-- account.tax.code.template -->
EOF
# id,name,code,parent_id,notprintable,sign
grep -v '^"id' "$DIR/account.tax.code.template.csv" | \
  dos2unix | \
  sed -f commas_in_csv.sed | \
  while read id name code parent_id notprintable sign ; do
cat << EOF
        <record id="$id" model="account.tax.code.template">
            <field name="name">$name</field>
            <field name="code">$code</field>
EOF
  if [ -z "$parent_id" ] ; then
cat << EOF
            <field name="parent_id" eval="False"/>
EOF
      true
    else
cat << EOF
            <field name="parent_id" ref="$parent_id"/>
            <field name="notprintable" eval="$notprintable"/>
EOF
    fi
  if [ "$sign" -ne 0 ] ; then
cat << EOF
            <field name="sign" eval="$sign"/>
EOF
    fi
cat << EOF
        </record>
EOF
done

# account.tax.template.csv
cat << EOF

        <!-- account.tax.template -->
EOF
# id,description,chart_template_id,type_tax_use,name,type,amount,account_collected_id,account_paid_id,base_code_id,tax_code_id,ref_base_code_id,ref_tax_code_id,tax_sign,base_sign,ref_base_sign,ref_tax_sign,parent_id
grep -v '^"id' "$DIR/account.tax.template.csv" | \
  dos2unix | \
  sed -f commas_in_csv.sed | \
  while read id description chart_template_id type_tax_use name type amount account_collected_id account_paid_id base_code_id tax_code_id ref_base_code_id ref_tax_code_id tax_sign base_sign ref_base_sign ref_tax_sign parent_id ; do
cat << EOF
        <record id="$id" model="account.tax.template">
            <field name="chart_template_id" ref="$chart_template_id"/>
            <field name="name">$name</field>
            <field name="description">$description</field>
            <field eval="$amount" name="amount"/>
            <field name="type">$type</field>
            <field name="account_collected_id" ref="$account_collected_id"/>
            <field name="account_paid_id" ref="$account_paid_id"/>
            <field name="base_code_id" ref="$base_code_id"/>
            <field name="ref_base_code_id" ref="$ref_base_code_id"/>
            <field name="tax_code_id" ref="$tax_code_id"/> <!-- ? -->
            <field name="ref_tax_code_id" ref="$ref_tax_code_id"/> <!-- ? -->
	    <field name="base_sign" eval="$base_sign"/>
	    <field name="ref_base_sign" eval="$ref_base_sign"/>
	    <field name="tax_sign" eval="$tax_sign"/>
	    <field name="ref_tax_sign" eval="$ref_tax_sign"/>
            <field name="tax_code_id" ref="$tax_code_id"/> <!-- ? -->
            <field name="type_tax_use">$type_tax_use</field>
EOF
  if [ -n "$parent_id" ] ; then
cat << EOF
            <field name="parent_id" ref="$parent_id"/>
EOF
    fi
cat << EOF
        </record>
EOF
done

cat << EOF

    </data>
</openerp>
EOF
