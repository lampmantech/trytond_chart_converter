# -*- encoding: utf-8 -*-

# If you have Oerp 7.0 installed, set the path to the addons
# as OERP_7_ADDONS in charts/Makefile
# If you have Oerp 6.0.4 installed, set the path to the addons
# as OERP_6_ADDONS in charts/Makefile

test::
	(cd charts && \
	    env PWD="${PWD}/charts " OERP_7_ADDONS=${OERP_7_ADDONS} \
		$(MAKE) $(MFLAGS) $@ )

add:: log
	git status|grep modified|sed -e 's/.*modified://'|xargs git add

log:: clean
	git log | grep -v ^Author > CHANGELOG.txt

clean::
	find . -type f -name \*~ -exec rm -f '{}' \;

veryclean:: clean
	(cd charts && \
		$(MAKE) $(MFLAGS) $@ )
