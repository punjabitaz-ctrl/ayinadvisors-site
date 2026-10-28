<main id="main" tabindex="-1">
<!-- CONTACT -->
<header class="contact-hero surface-inverse">
  <canvas id="iris"></canvas>
  <div class="contact-grid">
    <div class="contact-intro">
      <span class="eyebrow on-navy reveal"><svg class="iris-mark" viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="1.2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="5.2"/><circle cx="12" cy="12" r="1.8" fill="currentColor" stroke="none"/></svg>Book a Consultation</span>
      <h1 class="display reveal" data-d="1" style="font-size:clamp(2.6rem,5.4vw,4.6rem)">Let us see where<br />to begin.</h1>
      <p class="lead reveal" data-d="2">Tell us where you're headed. We'll come back within two business days with a candid first view - and the shape of an engagement if it's a fit.</p>
      <div class="contact-meta reveal" data-d="3">
        <div class="cmeta"><span class="k">Email</span><span class="v"><a href="mailto:hello@ayinadvisors.com">hello@ayinadvisors.com</a></span></div>
        <div class="cmeta"><span class="k">Call</span><span class="v"><a href="https://calendar.app.google/8iyzRwWpo7FWfYB98" target="_blank" rel="nofollow noopener noreferrer">Pick a time on the calendar<span class="vh"> (opens in a new tab)</span></a><small>Skip the form and book directly</small></span></div>
        <div class="cmeta"><span class="k">Offices</span><span class="v">New York<small>By appointment</small></span></div>
        <div class="cmeta"><span class="k">Response</span><span class="v">Within 2 business days</span></div>
      </div>
    </div>

    <div class="form-card reveal" data-d="2" id="book">
      <form id="consult-form" novalidate>
        <h2>Request a consultation</h2>
        <p class="sub">No obligation - a focused conversation about what you are trying to do.</p>
        <!-- honeypot: hidden from humans, catches bots -->
        <div class="hp" aria-hidden="true"><label for="company_url">Leave this blank</label><input id="company_url" name="company_url" type="text" tabindex="-1" autocomplete="off" /></div>
        <input type="hidden" id="interests" name="interests" value="" />
        <input type="hidden" name="_subject" value="New consultation request - AYiN Advisors" />
        <div class="field-row">
          <div class="field"><label for="name">Full name</label><input id="name" name="name" type="text" placeholder="Your name" required /></div>
          <div class="field"><label for="company">Company</label><input id="company" name="company" type="text" placeholder="Company name" required /></div>
        </div>
        <div class="field-row">
          <div class="field"><label for="email">Work email</label><input id="email" name="email" type="email" placeholder="you@company.com" required /></div>
          <div class="field"><label for="hq">Headquartered in</label><input id="hq" name="hq" type="text" placeholder="Country / region" /></div>
        </div>
        <div class="field">
          <label>Area of interest</label>
          <div class="chips" id="chips">
            <button type="button" class="chip" data-v="B2B Partnerships" data-practice="partnerships" aria-pressed="false">B2B Partnerships</button>
            <button type="button" class="chip" data-v="AI Solutions Development" data-practice="ai-solutions" aria-pressed="false">AI Solutions</button>
            <button type="button" class="chip" data-v="Digital Presence" data-practice="digital-presence" aria-pressed="false">Digital Presence</button>
            <button type="button" class="chip" data-v="Not sure yet" aria-pressed="false">Not sure yet</button>
          </div>
        </div>
        <div class="field"><label for="msg">What are you trying to achieve?</label><textarea id="msg" name="msg" placeholder="A few lines about your business and what you want to change…"></textarea></div>
        <div id="ct-turnstile" class="ct-turnstile"></div>
        <p class="form-error" id="form-error" role="alert"></p>
        <button type="submit" class="btn" data-magnetic="0.25"><span class="btn-label">Send Request</span><span class="btn-arrow">→</span></button>
      </form>
      <div class="form-success" id="success">
        <svg class="check" viewBox="0 0 80 80" aria-hidden="true"><circle cx="40" cy="40" r="36"></circle><path d="M25 41l11 11 20-22"></path></svg>
        <h2>Request received.</h2>
        <p>Thank you - we'll be in touch within two business days to find a time.</p>
      </div>
    </div>
  </div>
</header>
</main>
