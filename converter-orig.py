#!/bin/python

# convert OpenERP chart of accounts to Tryton format

import sys
import lxml.etree as ET
from lxml.builder import ElementMaker

INFILE="account_chart_netherlands.xml"
OUTFILE="account_nl.xml"


class Converter(object):
    """
    >>> c = Converter(INFILE)
    >>> c.intree
    <lxml.etree._ElementTree object at ...>
    
    >>> t = c.maker
    >>> x = t.tryton(t.data(t.record(model="account.account.type.template",id="nl")))
    >>> print c.render(x)
    <tryton>
      <data>
        <record model="account.account.type.template" id="nl"/>
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
                m.field("Dutch Account Type Chart", name='name'),
                m.field(name="sequence", eval="10"),
                model='account.account.type.template', id='nl',
            )
        )
        for e in self.intree.xpath("/openerp/data/record[@model='account.account.type']"):
            f = []
            id = e.get("id")
            name = e.xpath("field[@name='name']")[0].text
            closemethod = e.xpath("field[@name='close_method']")[0].text
            f.append(m.field(name, name='name'))
            f.append(m.field(name='sequence', eval=str(seq)))
            f.append(m.field(name='parent', ref='nl'))
            if closemethod == 'balance':
                f.append(m.field(name='balance_sheet', eval="True"))
            f = tuple(f)
            seq += 10
            r.append(m.record(*f, model='account.account.type.template', id=id))
        return r


    def build_account_template(self):
        # account.account.template
        m = self.maker
        r = []
        r.append(
            m.record(
                m.field("NEDERLANDS STANDAARD GROOTBOEKSCHEMA", name="name"),
                m.field("view", name="kind"),
                m.field(name="type", ref="nl"),
                id="root_nl", 
                model="account.account.template",
            )
        )
        l = self.intree.xpath("/openerp/data/record[@model='account.account.template']")
        for e in l:
            id = e.get("id")
            if id == 'a_root':
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

            if ref == 'user_type_income':
                kind = 'revenue'
            elif ref == 'user_type_expense':
                kind = 'expense'

            f.append(m.field(kind, name='kind'))

            if reconcile:
                reconcile = str(eval(reconcile[0].get("eval")))
                f.append(m.field(name='reconcile', eval=reconcile))

            if parent:
                parent = parent[0].get("ref")
                if parent == 'a_root':
                    parent = 'root_nl'
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
            if parent[0].get("eval"):
                if not eval(parent[0].get("eval")):
                    origroot=id
                    r.append(
                        m.record(
                            m.field(name, name='name'),
                            m.field(name='account',ref='root_nl'),
                            model="account.tax.code.template",
                            id="tax_code_nl"
                        )
                    )
                    continue

            f.append(m.field(name, name='name'))
            f.append(m.field(name='account',ref='root_nl'))

            parent = parent[0].get("ref")
            if parent == origroot:
                parent = "tax_code_nl"
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
                m.field("B.T.W. Verkoop", name="name"),
                m.field("B.T.W. Verkoop", name="code"),
                model="account.tax.group",
                id="tax_group_sale",
            )
        )
        r.append(
            m.record(
                m.field("B.T.W. Inkoop", name="name"),
                m.field("B.T.W. Inkoop", name="code"),
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

            f.append(m.field(name='account', ref='root_nl'))

            f = tuple(f)
            r.append(
                m.record(*f, id=id, model=model)
            )

        return r

    def build_tax_rule_template(self):
        model="account.tax.rule.template"
        m = self.maker
        return [
            m.record(
                m.field("Levering binnenland", name="name"),
                m.field(ref="root_nl", name="account"),
                model=model, 
                id="tax_rule_1",
            ),
            m.record(
                m.field("Verleggingsregelingen binnenland", name="name"),
                m.field(ref="root_nl", name="account"),
                model=model,
                id="tax_rule_2",
            ),
            m.record(
                m.field("Prestaties naar of in het buitenland", name="name"),
                m.field(ref="root_nl", name="account"),
                model=model,
                id="tax_rule_3",
            ),
            m.record(
                m.field("Levering vanuit buitenland", name="name"),
                m.field(ref="root_nl", name="account"),
                model=model,
                id="tax_rule_4",
            ),
        ]

    def build_tax_rule_line_template(self):
        model="account.tax.rule.line.template"
        m = self.maker
        return [
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

    def write(self, outfile=None):
        if not outfile:
            outfile = sys.stdout

        if type(outfile) == type("a"):
            outfile = open(outfile, 'w')

        outfile.write(self.render(self.outtree))
        outfile.flush()

    def render(self, e):
        return ET.tostring(e, encoding='UTF-8', pretty_print=True)


if __name__ == '__main__':
    if '--test' in sys.argv:
        import doctest
        doctest.testmod(optionflags=doctest.ELLIPSIS)
    else:
        c = Converter(INFILE)
        c.write(OUTFILE)


