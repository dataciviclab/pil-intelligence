# Makefile — pil-intelligence (compose mart-only)
#
# Layout: compose/{slug}/dataset.yml. Il compose è mart-only: legge dai
# clean/mart pubblicati su GCS (support type: external) e produce mart.

TOOLKIT = toolkit

COMPOSE := $(shell find compose -name dataset.yml 2>/dev/null | sort)

# --- Compose (mart-only) ----------------------------------------------------

.PHONY: run compose
run: compose

compose:
	@for f in $(COMPOSE); do \
		echo "=== $$f ==="; \
		$(TOOLKIT) run mart -c "$$f" -y 2026 || exit 1; \
	done

# --- Validazione config -----------------------------------------------------

.PHONY: check
check:
	@for f in $(COMPOSE); do \
		echo "→ $$f"; \
		$(TOOLKIT) run preflight -c "$$f" > /dev/null 2>&1 || exit 1; \
	done
	@echo "✅ All configs valid"

# --- Registry (artifact catalogo — dry-run di default) ----------------------

.PHONY: registry registry-write
registry:
	$(TOOLKIT) registry build --prefix pil-intelligence

registry-write:
	$(TOOLKIT) registry build --prefix pil-intelligence --write

# --- Dashboard --------------------------------------------------------------

.PHONY: dashboard
dashboard:
	cd dashboard && streamlit run app.py

# --- Pulizia ----------------------------------------------------------------

.PHONY: clean
clean:
	rm -rf out/data/_runs out/data/mart out/data/clean

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:' Makefile | sort
