# -*- encoding: utf-8 -*-
"""
This is a converter to convert OpenERP chart of accounts in XML
to Tryton's format based on the converter by Paul J. Stevens:
http://github.com/pjstevns/trytond_account_nl/

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
                   help="the Tryton output XML file to convert to")
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

# used by --test doctest only
INFILE="charts/l10n_uk_smartmode.xml"

# quick and dirty
dLang=dict()
dLang['en']=dict()
dLang['nl']=dict()

## hardwired ids
## FixMe: how much of these are coming from the chart itself?
## For now, I think it's best to mover them all to the config file.

## I think these could be found by code=0 but that may be just a convention
##moved dLang['nl']['A_ROOT_ID']='a_root'
##moved dLang['en']['A_ROOT_ID']='UK0'

dLang['nl']['ROOT_ACCOUNT_TEMPLATE_ID']='root_nl'
dLang['en']['ROOT_ACCOUNT_TEMPLATE_ID']='root_uk'
dLang['nl']['ACCOUNT_TYPE_TEMPLATE_ID']='nl'
dLang['en']['ACCOUNT_TYPE_TEMPLATE_ID']='uk'
dLang['nl']['ACCOUNT_TYPE_TEMPLATE_TYPE']='nl'
dLang['en']['ACCOUNT_TYPE_TEMPLATE_TYPE']='uk'
dLang['nl']['TAX_CODE_TEMPLATE_ID']="tax_code_nl"
dLang['en']['TAX_CODE_TEMPLATE_ID']="tax_code_uk"

## arbitrary names - t
dLang['nl']['ROOT_ACCOUNT_TEMPLATE_NAME']="NEDERLANDS STANDAARD GROOTBOEKSCHEMA"
dLang['en']['ROOT_ACCOUNT_TEMPLATE_NAME']="UK Standard Account Schema"
dLang['nl']['ACCOUNT_TYPE_TEMPLATE_NAME']="Dutch Account Type Chart"
dLang['en']['ACCOUNT_TYPE_TEMPLATE_NAME']="UK Account Type Chart"
dLang['nl']['TAX_GROUP_SALES_NAME']="B.T.W. Verkoop"
dLang['en']['TAX_GROUP_SALES_NAME']="V.A.T. on Sales"
dLang['nl']['TAX_GROUP_PURCHASES_NAME']="B.T.W. Inkoop"
dLang['en']['TAX_GROUP_PURCHASES_NAME']="V.A.T. on Purchases"
dLang['nl']['TAX_RULE_1_NAME']="Levering binnenland"
dLang['en']['TAX_RULE_1_NAME']="Delivery Inland"
dLang['nl']['TAX_RULE_2_NAME']="Verleggingsregelingen binnenland"
## FixMe: nonsense in English
dLang['en']['TAX_RULE_2_NAME']="Diversion Schemes inland"
dLang['nl']['TAX_RULE_3_NAME']="Prestaties naar of in het buitenland"
dLang['en']['TAX_RULE_3_NAME']="Sales to abroad"
dLang['nl']['TAX_RULE_4_NAME']="Levering vanuit buitenland"
dLang['en']['TAX_RULE_4_NAME']="Purchases from abroad"

CURRENT_LANG='en'
def _(sString): return dLang[CURRENT_LANG][sString]

class Converter(object):
    """
    >>> c = Converter(INFILE)
    >>> c.intree
    <lxml.etree._ElementTree object at ...>
    
    >>> t = c.maker
    >>> x = t.tryton(t.data(t.record(model="account.account.type.template",id="uk")))
    >>> print c.render(x)
    <tryton>
      <data>
        <record model="account.account.type.template" id="uk"/>
      </data>
    </tryton>
    <BLANKLINE>
    """

    def __init__(self, infile):
        self.intree = ET.parse(infile)
        self.maker = ElementMaker()
        tree = []
        tree += self.build_account_type_template()
        tree += self.build_account_template()
        tree += self.build_tax_code_template()
        tree += self.build_tax_group()
        tree += self.build_tax_template()
        tree += self.build_tax_rule_template()
        tree += self.build_tax_rule_line_template()
        tree = tuple(tree)

        m = self.maker
        self.outtree = m.tryton(m.data(*tree))

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
        dAccountAccountTemplate=dict(oConfig.items('account.account.template'))
        dChartConfig=dict(oConfig.items('chart'))
        assert 'a_root_id' in dChartConfig, "a_root_id not in dChartConfig %r" \
            % (dChartConfig.keys(),)
        
        m = self.maker
        r = []
        r.append(
            m.record(
                m.field(_('ROOT_ACCOUNT_TEMPLATE_NAME'), name="name"),
                m.field("view", name="kind"),
                m.field(name="type", ref=_('ACCOUNT_TYPE_TEMPLATE_TYPE')),
                id=_('ROOT_ACCOUNT_TEMPLATE_ID'), 
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
            typ = e.xpath("field[@name='user_type']")
            reconcile = e.xpath("field[@name='reconcile']")
            parent = e.xpath("field[@name='parent_id']")
            f = []
            f.append(m.field(name, name='name'))
            f.append(m.field(code, name='code'))
            ref = None
            if typ:
                ref = typ[0].get("ref")
                f.append(m.field(name='type',ref=ref))

            # FixMe: these are only conventional in Oerp
            ## some charts use account_type_income account_type_expense
            if ref == dAccountAccountTemplate['account_type_income']:
                kind = 'revenue'
            elif ref == dAccountAccountTemplate['account_type_expense']:
                kind = 'expense'
            ## what about 'user_type_asset' or ref == 'account_type_asset'

            ## liquidity kind does not exist - use other?
            ## if kind == 'liquidity': kind = 'other'
            
            f.append(m.field(kind, name='kind'))

            if reconcile:
                reconcile = str(eval(reconcile[0].get("eval")))
                f.append(m.field(name='reconcile', eval=reconcile))

            if parent:
                parent = parent[0].get("ref")
                if parent == dChartConfig['a_root_id']:
                    parent = _('ROOT_ACCOUNT_TEMPLATE_ID')
                f.append(m.field(name='parent', ref=parent))
            f = tuple(f)
            r.append(m.record(*f, model='account.account.template', id=id))
        return r

    def build_tax_code_template(self):
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
            if not parent: continue
            assert name, "Null name in account.tax.code.template for id="+id+' '+repr(e.text)
            if parent[0].get("eval"):
                if not eval(parent[0].get("eval")):
                    origroot=id
                    r.append(
                        m.record(
                            m.field(name, name='name'),
                            m.field(name='account', ref=_('ROOT_ACCOUNT_TEMPLATE_ID')),
                            model="account.tax.code.template",
                            id=_('TAX_CODE_TEMPLATE_ID')
                        )
                    )
                    continue

            f.append(m.field(name, name='name'))
            f.append(m.field(name='account', ref=_('ROOT_ACCOUNT_TEMPLATE_ID')))

            parent = parent[0].get("ref")
            if parent == origroot:
                parent = _('TAX_CODE_TEMPLATE_ID')
            f.append(m.field(name='parent', ref=parent))
        
            if code:
                code = code[0].text
                f.append(m.field(code, name='code'))

            f = tuple(f)
            r.append(m.record(*f, model='account.tax.code.template', id=id))

        return r

    def build_tax_group(self):
        m = self.maker
        r = []
        r.append(
            m.record(
                m.field(_('TAX_GROUP_SALES_NAME'), name="name"),
                m.field(_('TAX_GROUP_SALES_NAME'), name="code"),
                model="account.tax.group",
                id="tax_group_sale",
            )
        )
        r.append(
            m.record(
                m.field(_('TAX_GROUP_PURCHASES_NAME'), name="name"),
                m.field(_('TAX_GROUP_PURCHASES_NAME'), name="code"),
                model="account.tax.group",
                id="tax_group_purchase",
            )
        )
        return r

    def build_tax_template(self):
        model="account.tax.template"
        l = self.intree.xpath("/openerp/data/record[@model='%s']" % model)
        m = self.maker
        r = []
        for e in l:
            f = []
            id = e.get("id")
            name               = e.xpath("field[@name='name']")[0].text
            f.append(m.field(name, name='name'))
            
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
                    m.field(
                        name='invoice_account',ref=account_collected
                    )
                )

            account_paid       = e.xpath("field[@name='account_paid_id']")
            if account_paid: 
                account_paid = account_paid[0].get("ref")
                f.append(
                    m.field(
                        name='credit_note_account',
                        ref=account_paid
                    )
                )
            
            if account_collected and account_paid:

                amount             = e.xpath("field[@name='amount']")
                if amount: 
                    amount = int(float(amount[0].get("eval")) * 100)
                    f.append(
                        m.field(
                            name='percentage', 
                            eval="Decimal('%d')" % amount,
                        )
                    )
                    f.append(m.field('percentage', name='type'))

                tax_code           = e.xpath("field[@name='tax_code_id']")
                if tax_code: 
                    tax_code = tax_code[0].get("ref")
                    f.append(m.field(name='invoice_base_code', ref=tax_code))
                    f.append(m.field(name='invoice_tax_code', ref=tax_code))

                tax_sign           = e.xpath("field[@name='tax_sign']")
                if tax_sign: 
                    tax_sign = tax_sign[0].get("eval")
                    f.append(m.field(name='invoice_tax_sign', eval=tax_sign))

                base_sign          = e.xpath("field[@name='base_sign']")
                if base_sign: 
                    base_sign = base_sign[0].get("eval")
                    f.append(m.field(name='invoice_base_sign', eval=base_sign))
               
                ref_tax_code       = e.xpath("field[@name='ref_tax_code_id']")
                if ref_tax_code: 
                    ref_tax_code = ref_tax_code[0].get("ref")
                    f.append(m.field(name='credit_note_base_code', ref=ref_tax_code))
                    f.append(m.field(name='credit_note_tax_code', ref=ref_tax_code))

                ref_base_sign      = e.xpath("field[@name='ref_base_sign']")
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
            f.append(m.field(name='group', ref='tax_group_%s' % tax_type))

            f.append(m.field(name='account', ref=_('ROOT_ACCOUNT_TEMPLATE_ID')))

            f = tuple(f)
            r.append(
                m.record(*f, id=id, model=model)
            )

        return r

    def build_tax_rule_template(self):
        model="account.tax.rule.template"
        m = self.maker
        ## FixMe: these should be in the chart, not the converter
        return [
            m.record(
                m.field(_('TAX_RULE_1_NAME'), name="name"),
                m.field(ref=_('ROOT_ACCOUNT_TEMPLATE_ID'), name="account"),
                model=model, 
                id="tax_rule_1",
            ),
            m.record(
                m.field(_('TAX_RULE_2_NAME'), name="name"),
                m.field(ref=_('ROOT_ACCOUNT_TEMPLATE_ID'), name="account"),
                model=model,
                id="tax_rule_2",
            ),
            m.record(
                m.field(_('TAX_RULE_3_NAME'), name="name"),
                m.field(ref=_('ROOT_ACCOUNT_TEMPLATE_ID'), name="account"),
                model=model,
                id="tax_rule_3",
            ),
            m.record(
                m.field(_('TAX_RULE_4_NAME'), name="name"),
                m.field(ref=_('ROOT_ACCOUNT_TEMPLATE_ID'), name="account"),
                model=model,
                id="tax_rule_4",
            ),
        ]

    def build_tax_rule_line_template(self):
        model="account.tax.rule.line.template"
        m = self.maker
        ## FixMe: these should be in the chart, not the converter
        lRetval = [
            ## 1. verkoop binnenland
            m.record(
                m.field(name="rule",ref="tax_rule_1"),
                m.field(name="group",ref="tax_group_sale"),
                m.field(name="tax",ref="btw_0"),
                model=model, id="tax_rule_line_1_0"
            ),
            m.record(
                m.field(name="rule",ref="tax_rule_1"),
                m.field(name="group",ref="tax_group_sale"),
                m.field(name="tax",ref="btw_6"),
                model=model, id="tax_rule_line_1_6",
            ),
            m.record(
                m.field(name="rule",ref="tax_rule_1"),
                m.field(name="group",ref="tax_group_sale"),
                m.field(name="tax",ref="btw_19"),
                model=model, id="tax_rule_line_1_19"
            ),

            ## 3. export
            m.record(
                m.field(name="rule", ref="tax_rule_3"),
                m.field(name="group", ref="tax_group_sale"),
                m.field(name="tax", ref="btw_X0"),
                model=model, id="tax_rule_line_3_0",
            ),
            m.record(
                m.field(name="rule", ref="tax_rule_3"),
                m.field(name="group", ref="tax_group_sale"),
                m.field(name="tax", ref="btw_X1"),
                model=model, id="tax_rule_line_3_1",
            ),
            m.record(
                m.field(name="rule", ref="tax_rule_3"),
                m.field(name="group", ref="tax_group_sale"),
                m.field(name="tax", ref="btw_X2"),
                model=model, id="tax_rule_line_3_2",
            ),

            ## 4. import
            m.record(
                m.field(name="rule",ref="tax_rule_4"),
                m.field(name="group",ref="tax_group_purchase"),
                m.field(name="tax",ref="btw_E1_1"),
                model=model, id="tax_rule_line_4_1"
            ),
            m.record(
                m.field(name="rule",ref="tax_rule_4"),
                m.field(name="group",ref="tax_group_purchase"),
                m.field(name="tax", ref="btw_E2_1"),
                model=model, id="tax_rule_line_4_2"
            ),
            m.record(
                m.field(name="rule",ref="tax_rule_4"),
                m.field(name="group",ref="tax_group_purchase"),
                m.field(name="tax",ref="btw_E_overig_1"),
                model=model, id="tax_rule_line_4_overig"
            ),
        ]
        return lRetval

    def write(self, outfile=None):
        if not outfile:
            outfile = sys.stdout
        elif type(outfile) == type("a"):
            outfile = open(outfile, 'w')

        o = self.render(self.outtree)
        assert o
        outfile.write(o)
        outfile.flush()

    def render(self, e):
        return ET.tostring(e, encoding='UTF-8', pretty_print=True)

oConfig=None
def main(lArgs):
    global CURRENT_LANG, oConfig
    (oValues, lArguments) = oParser.parse_args(lArgs)
    
    CURRENT_LANG=oValues.sLang
    
    if oValues.bTest or '--test' in lArgs:
        import doctest
        ## FixMe: does doctest.testmod return an integer?
        return doctest.testmod(optionflags=doctest.ELLIPSIS)
    
    assert len(lArguments) == 1, __doc__
    sInfile=lArguments[0]
    assert os.path.exists(sInfile), "File not found: "+sInfile

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
    
    c = Converter(sInfile)
    c.write(oValues.sOutfile)
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
