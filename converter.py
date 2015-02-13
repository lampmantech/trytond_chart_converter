# -*- encoding: utf-8 -*-
"""This is a converter to convert OpenERP chart of accounts in XML
to Tryton's format based on the converter by Paul J. Stevens:
http://github.com/pjstevns/trytond_account_nl/

If you don't provide an --outfile option, then output is to stdout.
If you provide an --outfile option, but don't provide a --taxfile
option, then all output is to the outfile.  If you provide an --outfile
option and a --taxfile option, then the account info is output is to the
outfile, and the chart of taxes is output to the taxfile.

Splitting the two is generally a good idea, because the account chart
varies with the type of the company's business, but the tax chart is
the same for all companies within a country, state or province.

usage: %prog [options] INPUTFILE

"""

import sys, os
import lxml.etree as ET
from lxml.builder import ElementMaker
from optparse import OptionParser
from ConfigParser import ConfigParser

# build the options
usage = __doc__
oParser = OptionParser(usage=usage)
oParser.add_option("-o", "--outfile",
                   action="store", dest="sOutfile", type = "string",
                   default="",
                   help="the Tryton output XML file to convert to, defaults to stdout")
oParser.add_option("-x", "--taxfile",
                   action="store", dest="sTaxfile", type = "string",
                   default="",
                   help="the Tryton output XML file for taxes, if you want them separately")
oParser.add_option("-c", "--config",
                   action="store", dest="sConfigFile", type = "string",
                   default="",
                   help="the config file to govern the conversion (defaults to <lang>.cfg)")
oParser.add_option("-l", "--lang",
                   action="store", dest="sLang",
                   choices=['en','nl'],
                   default='en',
                   help="the language code to use: one of [en,nl]")
oParser.add_option("-t", "--test",
                   action="store_true", dest="bTest",
                   default=False,
                   help="run the doctests in this file")

# quick and dirty
dLang=dict()
dLang['en']=dict()
dLang['nl']=dict()

## hardwired ids
## FixMe: how much of these are coming from the chart itself?
## For now, I think it's best to mover them all to the config file.

##! model="account.chart.template" <field name="account_root_id" ref=
##moved dLang['nl']['A_ROOT_ID']='a_root'
##moved dLang['en']['A_ROOT_ID']='UK0'

dLang['nl']['ACCOUNT_TYPE_TEMPLATE_ID']='nl'
dLang['en']['ACCOUNT_TYPE_TEMPLATE_ID']='uk'
dLang['nl']['ACCOUNT_TYPE_TEMPLATE_NAME']="Dutch Account Type Chart"
dLang['en']['ACCOUNT_TYPE_TEMPLATE_NAME']="UK Account Type Chart"

dLang['nl']['TAX_CODE_TEMPLATE_ID']="tax_code_nl"
dLang['en']['TAX_CODE_TEMPLATE_ID']="tax_code_uk"

CURRENT_LANG='en'
def _(sString): return dLang[CURRENT_LANG][sString]

# the original input, used by --test doctest only
INFILE='charts/account_chart_netherlands.xml'

# From from trytond_account-3.2.1/account.py:
lTrytonAllowedKinds=['other',
		  'payable',
		  'revenue',
		  'receivable',
		  'expense',
		  'stock',
		  'view',
		  ]

class Converter(object):
    """
    """

    def __init__(self, infile, oConfig=None, oValues=None):
        self.oConfig = oConfig
        self.oValues = oValues

        self.intree = ET.parse(infile)
        self.maker = ElementMaker()
        tree = []
        tree += self.build_account_type_template()
        tree += self.build_account_template()
        lTaxTree = []
        lTaxTree += self.build_tax_code_template()
        lTaxTree += self.build_tax_group()
        lTaxTree += self.build_tax_template()
        lTaxTree += self.build_tax_rule_template()
        lTaxTree += self.build_tax_rule_line_template()

        if oValues and oValues.sTaxfile:
            tree = tuple(tree)
            self.outtree = self.maker.tryton(self.maker.data(*tree))
            lTaxTree = tuple(lTaxTree)
            self.taxtree = self.maker.tryton(self.maker.data(*lTaxTree))
        else:
            tree = tuple(tree+lTaxTree)
            self.outtree = self.maker.tryton(self.maker.data(*tree))
            self.taxtree = None

    def build_account_type_template(self):
        # account.account.type -> account.account.type.template
        m = self.maker
        r = []
        seq = 10
        r.append(
            m.record(
                m.field(_('ACCOUNT_TYPE_TEMPLATE_NAME'), name='name'),
                m.field(name="sequence", eval="10"),
                model='account.account.type.template',
                id=_('ACCOUNT_TYPE_TEMPLATE_ID'),
            )
        )
        for e in self.intree.xpath("/openerp/data/record[@model='account.account.type']"):
            f = []
            id = e.get("id")
            name = e.xpath("field[@name='name']")[0].text
            ## you can have account.account.type id="account_type_view"
            ## where the close_method is not required
            l = e.xpath("field[@name='close_method']")
            if l:
                closemethod = l[0].text
            else:
                closemethod = ''
            f.append(m.field(name, name='name'))
            f.append(m.field(name='sequence', eval=str(seq)))
            f.append(m.field(name='parent', ref=_('ACCOUNT_TYPE_TEMPLATE_ID')))
            if closemethod == 'balance':
                f.append(m.field(name='balance_sheet', eval="True"))
            f = tuple(f)
            seq += 10
            r.append(m.record(*f, model='account.account.type.template', id=id))
        return r


    def build_account_template(self):
        # account.account.template
        assert 'account.account.template' in self.oConfig.sections()
        dChartConfig=dict(self.oConfig.items('chart'))
        for s in ['a_root_id', 'root_account_template_name']:
            assert s in dChartConfig, "%s not in dChartConfig %r" \
                % (s, dChartConfig.keys(),)
        dAccountAccountTemplate=dict(self.oConfig.items('account.account.template'))
        for s in ['account_type_income', 'account_type_expense']:
            assert s in dAccountAccountTemplate, "%s not in dAccountAccountTemplate %r" \
                % (s, dAccountAccountTemplate.keys(),)
        m = self.maker
        r = []
        r.append(
            m.record(
                m.field(dChartConfig['root_account_template_name'], name="name"),
                m.field("view", name="kind"),
                m.field(name="type", ref=dChartConfig['root_account_template_type']),
                m.field(dChartConfig['root_account_template_id'], name="code"),
                id=dChartConfig['root_account_template_id'],
                model="account.account.template",
            )
        )
        l = self.intree.xpath("/openerp/data/record[@model='account.account.template']")
        for e in l:
            id = e.get("id")
            if id == dChartConfig['a_root_id']:
                continue
            name = e.xpath("field[@name='name']")[0].text
            code = e.xpath("field[@name='code']")[0].text
            kind = e.xpath("field[@name='type']")[0].text
            user_type = e.xpath("field[@name='user_type']")
            reconcile = e.xpath("field[@name='reconcile']")
            parent = e.xpath("field[@name='parent_id']")
                
            f = []
            f.append(m.field(name, name='name'))
            f.append(m.field(code, name='code'))
            ref = None
            if user_type:
                ref = user_type[0].get("ref")
                f.append(m.field(name='type',ref=ref))

            # These names are only conventional in Oerp
            if ref == dAccountAccountTemplate['account_type_income']:
                kind = 'revenue'
            elif ref == dAccountAccountTemplate['account_type_expense']:
                #? what about COGS - is it kind=other and type=expense?
                #?if kind != 'other':
                kind = 'expense'
            elif ref == "account_type_output_tax":
                #? liability
                kind = "other"
                #? "Unreconciled" why not balance?
            elif ref == "account_type_input_tax":
                #? asset
                kind = "other"
                #? "Unreconciled" why not balance?

            ##? liquidity kind does not exist in Tryton - use other?
            if kind == 'liquidity': kind = 'other'

            ##? stock kind does not exist in Oerp - use other?
            if kind != 'view' and name.lower().startswith('stock'):
                # FixMe: this is gross
                kind = 'stock'

            assert kind in lTrytonAllowedKinds, \
                "%s not in lTrytonAllowedKinds %r" % (kind, lTrytonAllowedKinds,)
            f.append(m.field(kind, name='kind'))

            if reconcile:
                reconcile = str(eval(reconcile[0].get("eval")))
                f.append(m.field(name='reconcile', eval=reconcile))

            if parent:
                parent = parent[0].get("ref")
                if parent == dChartConfig['a_root_id']:
                    parent = dChartConfig['root_account_template_id']
            else:
                # should only be one of these
                parent=dChartConfig['root_account_template_id']
            f.append(m.field(name='parent', ref=parent))
            
            f = tuple(f)
            r.append(m.record(*f, model='account.account.template', id=id))
        return r

    def build_tax_code_template(self):
        dChartConfig=dict(self.oConfig.items('chart'))
        for s in ['root_account_template_id']:
            assert s in dChartConfig, "%s not in dChartConfig %r" \
                % (s, dChartConfig.keys(),)

        l = self.intree.xpath("/openerp/data/record[@model='account.tax.code.template']")
        m = self.maker
        r = []
        origroot = None
        for e in l:
            f = []
            id = e.get("id")
            name = e.xpath("field[@name='name']")[0].text
            code = e.xpath("field[@name='code']")
            parent = e.xpath("field[@name='parent_id']")
            if not parent:
                #? why - not append?
                continue
            assert name, "Null name in account.tax.code.template for id="+id+' '+repr(e.text)
            if parent[0].get("eval"):
                if not eval(parent[0].get("eval")):
                    origroot=id
                    r.append(
                        m.record(
                            m.field(name, name='name'),
                            m.field(name='account', ref=dChartConfig['root_account_template_id']),
                            model="account.tax.code.template",
                            id=_('TAX_CODE_TEMPLATE_ID')
                        )
                    )
                    continue

            f.append(m.field(name, name='name'))
            f.append(m.field(name='account',
                             ref=dChartConfig['root_account_template_id']))

            parent = parent[0].get("ref")
            if parent == origroot:
                parent = _('TAX_CODE_TEMPLATE_ID')
            f.append(m.field(name='parent', ref=parent))

            if code:
                code = code[0].text
                f.append(m.field(code, name='code'))
            #? "notprintable","sign"
            f = tuple(f)
            r.append(m.record(*f, model='account.tax.code.template', id=id))

        return r

    def build_tax_group(self):
        model="account.tax.group"
        if not self.oConfig.has_section(model): return []

        dTaxGroup=dict(self.oConfig.items(model))
        sFile=dTaxGroup['xmlfile']
        print sFile
        assert os.path.exists(sFile), "File not found: "+sFile
        oSubTree=ET.parse(sFile)

        l = oSubTree.xpath("/tryton/data/record[@model='%s']" % model)
        # ??
        return l
    
        m = self.maker
        r = []
        for e in l:
            f = []
            id = e.get("id")
            name = e.xpath("field[@name='name']")[0].text
            f.append(m.field(name, name='name'))
            for sElt in ['code']:
                sText = e.xpath("field[@name='"+sElt+"']")[0].text
                f.append(m.field(sText, name=sElt))
            f = tuple(f)
            r.append(
                m.record(*f, id=id, model=model)
            )

        return r

    def build_tax_template(self):
        dChartConfig=dict(self.oConfig.items('chart'))
        model="account.tax.template"
        l = self.intree.xpath("/openerp/data/record[@model='%s']" % model)
        m = self.maker
        r = []
        for e in l:
            f = []
            id = e.get("id")
            name               = e.xpath("field[@name='name']")[0].text
            f.append(m.field(name, name='name'))
            try:
                description        = e.xpath("field[@name='description']")
                if description:
                    description = description[0].text
                    f.append(m.field(description, name='description'))
                else:
                    f.append(m.field(name, name='description'))
                account_collected  = e.xpath("field[@name='account_collected_id']")
                if account_collected:
                    account_collected = account_collected[0].get("ref")
                    f.append(
                        m.field(search="[('code', '=', '%s')]" % \
                                (account_collected,),
                                model='account.account.template',
                                name='invoice_account',
                        )
                    )

                account_paid       = e.xpath("field[@name='account_paid_id']")
                if account_paid:
                    account_paid = account_paid[0].get("ref")
                    f.append(
                        m.field(
                            search="[('code', '=', '%s')]" % \
                                                 (account_paid,),
                            model='account.account.template',
                            name='credit_note_account',
                        )
                    )

                if account_collected and account_paid:

                    amount             = e.xpath("field[@name='amount']")
                    if amount:
                        if 'eval' in amount[0].keys():
                            g = amount[0].get("eval")
                        else:
                            g = amount[0].text
                        amount = float(g)
                        f.append(
                            m.field(
                                name='rate',
                                eval="Decimal('%2.2f')" % amount,
                            )
                        )
                        f.append(m.field('percentage', name='type'))

                    base_code = e.xpath("field[@name='base_code_id']")
                    if base_code:
                        base_code = base_code[0].get("ref")
                        f.append(m.field(search="[('code', '=', '%s')]" % \
                                                 (base_code,),
                                         model='account.tax.code.template',
                                         name='invoice_base_code',
                                     )
                        )
                    tax_code           = e.xpath("field[@name='tax_code_id']")
                    if tax_code:
                        tax_code = tax_code[0].get("ref")
                        f.append(m.field(search="[('code', '=', '%s')]" % \
                                                 (tax_code,),
                                         model='account.tax.code.template',
                                         name='invoice_tax_code',
                                     )
                        )

                    tax_sign = e.xpath("field[@name='tax_sign']")
                    if tax_sign:
                        tax_sign = tax_sign[0].get("eval")
                        f.append(m.field(name='invoice_tax_sign', eval=tax_sign))

                    base_sign          = e.xpath("field[@name='base_sign']")
                    if base_sign:
                        base_sign = base_sign[0].get("eval")
                        f.append(m.field(name='invoice_base_sign', eval=base_sign))

                    ref_base_code = e.xpath("field[@name='ref_base_code_id']")
                    if base_code:
                        ref_base_code = ref_base_code[0].get("ref")
                        f.append(m.field(search="[('code', '=', '%s')]" % \
                                                 (ref_base_code,),
                                         model='account.tax.code.template',
                                         name='credit_note_base_code',
                                     )
                        )
                    ref_tax_code       = e.xpath("field[@name='ref_tax_code_id']")
                    if ref_tax_code:
                        ref_tax_code = ref_tax_code[0].get("ref")
                        f.append(m.field(search="[('code', '=', '%s')]" % \
                                                 (ref_tax_code,),
                                         model='account.tax.code.template',
                                         name='credit_note_tax_code',
                                     )
                        )

                    ref_base_sign = e.xpath("field[@name='ref_base_sign']")
                    if ref_base_sign:
                        ref_base_sign = ref_base_sign[0].get("eval")
                        f.append(m.field(name='credit_note_base_sign', eval=ref_base_sign))

                    ref_tax_sign       = e.xpath("field[@name='ref_tax_sign']")
                    if ref_tax_sign:
                        ref_tax_sign = ref_tax_sign[0].get("eval")
                        f.append(m.field(name='credit_note_tax_sign', eval=ref_tax_sign))
                else:
                    f.append(m.field('none', name='type'))

                parent             = e.xpath("field[@name='parent_id']")
                if parent:
                    parent = parent[0].get("ref")
                    f.append(m.field(name='parent', ref=parent))

                tax_type           = e.xpath("field[@name='type_tax_use']")[0].text
                # openerp-7.0-20140125-002455/openerp/addons/account/account.py
                # 'type_tax_use': fields.selection([('sale','Sale'),('purchase','Purchase'),('all','All')], 'Tax Application', required=True)
                # this can be 'all'
                # this also hardwires the ids from the account.tax.group
                f.append(m.field(name='group', ref='tax_group_%s' % tax_type))

                f.append(m.field(name='account', ref=dChartConfig['root_account_template_id']))
                # VAT rates change with time, and OERP dont;
                # fill the field in as the beginning of computer time
                # to  signal it can ce changed, and then let others correct it
                f.append(m.field('1971-01-01', name='start_date'))
                # FixMe: a better way is to make changable taxes
                # children of a tax.template of kind-none
                # see tax_fr.xml
            except Exception, e:
                (type, value, traceback,) = sys.exc_info()
                value = "ID=%s " % (id,) + str(value)
                raise type, value, traceback
            f = tuple(f)
            r.append(
                m.record(*f, id=id, model=model)
            )

        return r

    def build_tax_rule_template(self):
        ## these should be in the chart, not the converter
        ## but at least now they are broken out to XML xmlfile files
        model="account.tax.rule.template"
        if not self.oConfig.has_section(model): return []

        dTaxRuleLineTemplate=dict(self.oConfig.items(model))
        sFile=dTaxRuleLineTemplate['xmlfile']
        if not os.path.exists(sFile):
            sFile = os.path.join(os.path.dirname(self.oConfig.sConfigFile),
                                 sFile)
        if not os.path.exists(sFile): return []
        assert os.path.exists(sFile), "File not found: "+sFile
        oSubTree=ET.parse(sFile)

        l = oSubTree.xpath("/tryton/data/record[@model='%s']" % model)
        #??
        return l
        m = self.maker
        r = []
        for e in l:
            f = []
            id = e.get("id")
            name = e.xpath("field[@name='name']")[0].text
            f.append(m.field(name, name='name'))
            for sElt in ['account']:
                sRef = e.xpath("field[@name='"+sElt+"']")[0].get('ref')
                f.append(m.field(name=sElt, ref=sRef))
            f = tuple(f)
            r.append(
                m.record(*f, id=id, model=model)
            )

        return r

    def build_tax_rule_line_template(self):
        ## these should be in the chart, not the converter
        ## but at least now they are broken out to XML xmlfile files
        model="account.tax.rule.line.template"
        if not self.oConfig.has_section(model): return []

        dTaxRuleLineTemplate=dict(self.oConfig.items(model))
        sFile=dTaxRuleLineTemplate['xmlfile']
        if not os.path.exists(sFile):
            sFile = os.path.join(os.path.dirname(self.oConfig.sConfigFile),
                                 sFile)
        if not os.path.exists(sFile): return []
        assert os.path.exists(sFile), "File not found: "+sFile
        oSubTree=ET.parse(sFile)

        l = oSubTree.xpath("/tryton/data/record[@model='%s']" % model)
        #??
        return l
        m = self.maker
        r = []
        for e in l:
            f = []
            id = e.get("id")
            for sElt in ['rule','group','tax']:
                sRef = e.xpath("field[@name='"+sElt+"']")[0].get('ref')
                f.append(m.field(name=sElt, ref=sRef))
            f = tuple(f)
            r.append(
                m.record(*f, id=id, model=model)
            )

        return r

    def write(self):
        outfile = self.oValues.sOutfile
        taxfile = self.oValues.sTaxfile
        if not outfile or outfile == '-':
            u = self.render(self.outtree)
            assert u
            sys.stdout.write(u)
            return

        if taxfile:
            u = self.render(self.taxtree)
            assert u
            with open(taxfile, 'wt') as oFd:
                oFd.write(u)
            # drop through

        u = self.render(self.outtree)
        assert u
        with open(outfile, 'wt') as oFd:
            oFd.write(u)

    def render(self, e):
        uRetval = ET.tostring(e, encoding='UTF-8', pretty_print=True,
                              xml_declaration=True)
        if uRetval.find('><') > 0:
            # grr- there has to be a way to pretty print the tax code
            uRetval = uRetval.replace("><field", ">\n      <field")
            uRetval = uRetval.replace("><", ">\n    <")
        return uRetval
    
def main(lArgs):
    global CURRENT_LANG
    (oValues, lArguments) = oParser.parse_args(lArgs)

    CURRENT_LANG=oValues.sLang

    if oValues.bTest or '--test' in lArgs:
        import doctest
        ## FixMe: does doctest.testmod return an integer?
        return doctest.testmod(optionflags=doctest.ELLIPSIS)

    if len(lArguments) == 1 and lArguments[0] != '-':
        sInfile=lArguments[0]
        assert os.path.exists(sInfile), "File not found: "+sInfile
    else:
        sInfile=sys.stdin

    ## FixMe: later on, maybe parse the chart for this info
    ## but for now, use a config file to specify the info.
    ## Im not convinced that all the info is there, or easy to find.
    sConfigFile=oValues.sConfigFile
    if not sConfigFile:
        ## provide a default based on the language
        ## that way we can provide some examples
        ## and hopefully standardize chart ids within a language
        sConfigFile=os.path.join(os.path.dirname(__file__),
                                 oValues.sLang+'.cfg')

    assert os.path.exists(sConfigFile), "File not found: "+sConfigFile
    oConfig = ConfigParser()
    oConfig.readfp(open(sConfigFile))
    oConfig.sConfigFile = sConfigFile

    c = Converter(sInfile, oConfig=oConfig, oValues=oValues)
    c.write()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
