# Third-party code shipped with the site

Everything here is self-hosted (no CDN at runtime). Exact versions and SHA-256 hashes are in `MANIFEST.json`
(`assets/vendor/`) and `assets/hero3d.build.json` (the Home hero bundle). Rebuild steps are in `DEPLOY.md`.

## Lenis (`lenis.min.js`) - MIT

The MIT License

Copyright (c) 2024 darkroom.engineering

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## GSAP and ScrollTrigger (`gsap.min.js`, `ScrollTrigger.min.js`) - GSAP Standard "no charge" licence

Copyright GreenSock / Webflow. Licence: https://gsap.com/standard-license (named in the package's own
`package.json` and in the licence banner at the top of each file). GSAP has been free to use, including commercially,
since Webflow acquired GreenSock in 2025. The licence text is not shipped inside the npm package, so it is linked here
rather than copied. The one restriction to know about: the licence does not permit using GSAP inside a product or tool
that lets other people build visual animations and competes with Webflow's own animation tools. A marketing site does not
fall under that. Re-read the licence at the URL before upgrading across a major version.

## three.js (bundled and tree-shaken into `assets/hero3d.js`) - MIT

The MIT License

Copyright © 2010-2026 three.js authors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
