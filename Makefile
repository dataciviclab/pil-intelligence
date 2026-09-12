TOOLKIT = toolkit

.PHONY: run
run:
	$(TOOLKIT) run mart -c dataset.yml -y 2026

.PHONY: check
check:
	$(TOOLKIT) run preflight -c dataset.yml > /dev/null 2>&1 || echo "⚠️  preflight failed"

.PHONY: clean
clean:
	rm -rf out/data/_runs out/data/mart

.PHONY: dashboard
dashboard:
	cd dashboard && streamlit run app.py

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:' Makefile | sort
