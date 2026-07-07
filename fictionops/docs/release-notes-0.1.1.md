# FictionOps 0.1.1 Release Notes

FictionOps 0.1.1 is a pre-alpha packaging and onboarding patch release.

The 0.1.0 milestone proved the core MVP and the TestPyPI release pipeline. This 0.1.1 candidate packages the later public-facing cleanup so the artifact intended for PyPI matches the current GitHub landing page, model-provider docs, citation metadata, quickstart preview, and release-candidate plan.

## Highlights

- Added a GitHub root README with positioning, quickstart commands, AI/API integration notes, documentation links, roadmap, citation, and license pointers.
- Added root `LICENSE` and `CITATION.cff`.
- Added a quickstart terminal preview SVG and included it in source distributions.
- Added OpenAI-compatible Chat Completions provider documentation and runner coverage for providers such as DeepSeek, Qwen/DashScope, Kimi/Moonshot, GLM/Zhipu, Doubao/Ark, SiliconFlow, OpenAI-compatible local servers, and OpenAI Chat Completions.
- Added promotion kit docs for GitHub Release, Show HN, community posts, Chinese article outlines, and demo scripting.
- Added quickstart/onboarding issue template and recommended GitHub labels.
- Updated package metadata URLs and keywords.
- Documented why the current public package candidate should be `0.1.1` rather than reusing the earlier `0.1.0` TestPyPI artifact.

## Install

From GitHub before PyPI publication:

```bash
python -m pip install "git+https://github.com/SouthWinter/fictionops.git#subdirectory=fictionops"
```

After PyPI publication:

```bash
python -m pip install fictionops
```

## Verification Target

The release candidate should pass:

```bash
python -m compileall -q fictionops/src fictionops/examples
python -m unittest discover -s fictionops/tests -v
python -m pip wheel ./fictionops -w fictionops/dist --no-deps --no-build-isolation
python -c "import os, pathlib, setuptools.build_meta as b; os.chdir('fictionops'); pathlib.Path('dist').mkdir(exist_ok=True); print(b.build_sdist('dist'))"
```

The TestPyPI evidence for this package version should be recorded separately from the historical 0.1.0 evidence.

