SHELL = /bin/bash

s3bucket = cudl-artefacts
s3keyBase = projects/cudl-packaging/dist/
s3UrlBase = "s3://$(s3bucket)/$(s3keyBase)"

default: package

package: export npm_config_color = always
package: build
# Refuse to build a package with local modifications, as the package may end up
# containing the modifications rather than the committed state.
	@DIRTY_FILES="$$(git status --porcelain)" ; \
	if [ "$$DIRTY_FILES" != "" ]; then \
		echo "Warning: git repo has uncommitted changes, package may not be reproducible:" ; \
		echo "$$DIRTY_FILES" ; \
	fi
	cd build && npm pack .. | tee npm-pkg-name

publish: package
	@DIRTY_FILES="$$(git status --porcelain)" ; \
	if [ "$$DIRTY_FILES" != "" ]; then \
		echo "Error: git repo has uncommitted changes, refusing to public package built from dirty files:" ; \
		echo "$$DIRTY_FILES" ; \
		exit 1 ; \
	fi
# Refuse to publish unless we get a 404 when looking up the publish path no S3.
# If the artefact already exists will be overwritten if FORCE_OVERWRITE_PACKAGE
# is set to the name of the archive being published.
	@if HEAD_RESP="$$(aws s3api head-object --bucket "$(s3bucket)" --key "$(s3keyBase)$$(cat build/npm-pkg-name)" 2>&1)"; then \
		echo "$$HEAD_RESP" ; \
		if [ "$$PUBLISH_FORCE_OVERWRITE_PACKAGE" ==  "$$(cat build/npm-pkg-name)" ] ; then \
			echo 'Package exists but overwrite requested via $$PUBLISH_FORCE_OVERWRITE_PACKAGE' ; \
		else \
			echo "$$(cat build/npm-pkg-name) is already published - refusing to overwrite" ; \
			exit 1 ; \
		fi ; \
	else \
		STATUS=$$? ; \
		if ! (echo "$$HEAD_RESP" | grep -Fq 'An error occurred (404) when calling the HeadObject operation: Not Found') ; then \
			echo "aws s3api head-object exited with status $$STATUS: $$HEAD_RESP" ; \
		fi ; \
	fi
	aws s3 cp \
		$$(if [[ "$$PUBLISH_DRYRUN" != "" ]] ; then echo --dryrun; fi) \
		"build/$$(cat build/npm-pkg-name)" s3://cudl-artefacts/projects/cudl-packaging/dist/

build:
	mkdir -p build

clean:
	rm -rf build

.PHONY: package clean
