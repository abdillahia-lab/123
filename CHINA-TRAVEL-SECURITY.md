# China Travel Security Advisory — Deep Edition

**Audience:** A cybersecurity consultant and startup founder (Jinki AI / BAHB —
autonomous drone inspection AI for data centers and substations) traveling to
mainland China for a conference. Threat tolerance: paranoid.

**How to read this:** Paranoid is the right setting for this trip — but
paranoia without calibration wastes effort on the wrong things. Each section
separates *what is certain* from *what is possible but unlikely*, so you spend
your attention where it changes outcomes. The §14 risk register is the
one-page calibration; the appendices are the build instructions.

---

## 0. Disclaimer

Operational-security guidance, **not legal advice**. Chinese law and its
enforcement change fast and are applied unevenly. Before you go:

- Read the **current US State Department China Travel Advisory** in full — the
  level and the specific language change; do not rely on memory.
- Enroll in **STEP** (Smart Traveler Enrollment Program).
- If you have, or have ever had, a **business dispute, contract, investment,
  or employment tie with any Chinese entity**, consult counsel before flying —
  that is the single biggest factor in exit-ban risk (§3.3).
- Carry the US Embassy Beijing and relevant US Consulate phone numbers on
  paper, not only on a device.

---

## 1. Executive summary

Your original plan, scored:

| Your idea | Verdict | Why | Do instead |
|---|---|---|---|
| Back up + leave your real phone in the US | **Correct** | A device that never enters China cannot be compromised there. | Keep it. Encrypted backup, powered off, stored securely at home. |
| Buy the phone *in China* | **Wrong** | Chinese-market firmware ships telemetry by default; 2026 firmware-malware targets exactly that profile; purchase requires passport registration anyway. | Buy a clean burner **in the US** and pre-provision it. |
| Log into WeChat | **Avoidable** | Not end-to-end encrypted; pervasive content surveillance; harvests contacts/location/device IDs on install. | Don't install it. Carry the conference ticket as a static QR image. |
| Log into Alipay | **OK, with discipline** | Real-name binding to your passport is unavoidable, but the rest of the footprint is controllable. | Burner-only, international card or TourCard, minimal data. |

**The one rule that matters most:** carry nothing technical across the border —
no tools, no client data, no source code, no site material. The malware risk
is real; the *legal* risk of being found with technical material is worse.

---

## 2. Threat model

### 2.1 The four adversaries and what each one wants

1. **The state** (Ministry of State Security, customs, network operators).
   Goal: intelligence collection and leverage. Capabilities: lawful intercept
   on every domestic network by design; warrantless border device inspection;
   biometric capture at entry; physical access to hotel rooms when motivated.
   This adversary is *passive-pervasive* by default and *active-targeted* if
   you are flagged.

2. **Commercial / industrial espionage.** Goal: your IP, customer list, site
   data, pricing, roadmap. Your sector — drone inspection of **critical
   infrastructure** plus geospatial/mapping data — is genuinely interesting
   here. This adversary may operate independently of, or in cooperation with,
   the state.

3. **Network interception.** Hotel, conference, and café Wi-Fi; possibly
   IMSI-catchers near venues. Goal: credentials and content in transit.

4. **Opportunistic crime.** Device theft, juice-jacking, malicious chargers,
   pickpocketing. Goal: the device and whatever is on it.

These overlap: a hotel-network capture (3) can feed a state file (1); a
conference contact (2) can be tasked by (1).

### 2.2 Data-value analysis — think in terms of what each asset *gives* them

Don't ask "is this device important?" Ask "what does an adversary *gain* if
they get it?" That reframes every packing decision:

| If they get… | They gain… | So the rule is… |
|---|---|---|
| Your primary phone | Your whole life: messages, photos, location history, every account with a saved session, your password manager | Never bring it. |
| A logged-in laptop | Corporate network access, source code, documents, cached credentials | Bring nothing, or a dumb terminal (§4.5). |
| Your real Apple/Google account | Cloud backups, contacts, the ability to push to other devices | Use a fresh, throwaway account on the burner. |
| Your authenticator app | A path into every account it protects | Keep critical-account 2FA *off* the burner. |
| Your contact list | A social graph — who you know, who to pressure, who to approach | Burner carries zero real contacts. |
| A WeChat login | A permanent passport-linked identity + contact/location harvest | Don't install it. |

The discipline isn't "protect the device." It's "make sure the device, if
fully lost, costs you nothing."

### 2.3 Your personal risk profile

You sit one tier above an ordinary tourist for two independent reasons:

- **You are a security consultant.** Penetration-testing tools, exploit code,
  scripts, or even security training material on a device crossing the border
  can be construed as "items related to national security" under the
  Counter-Espionage Law (§3.1). This is the easiest avoidable mistake.
- **You found a company in a sensitive sector.** Drones, critical
  infrastructure (data centers, substations), and mapping/geospatial data all
  touch areas China explicitly regulates as national-security relevant.
  Carrying site surveys, customer lists, or drone logs is the second easiest
  avoidable mistake.

### 2.4 Calibrate the paranoia

What is **near-certain** on this trip: every network you touch is monitored;
biometrics are captured at entry; WeChat/Alipay harvest data if installed; a
Chinese-firmware phone leaks telemetry.

What is **possible but not likely** for a short conference visit with no local
legal entanglement: a full border device-imaging; an Android border-app
install at a major airport (this is overwhelmingly a Xinjiang land-border
phenomenon — see §5.1); a targeted hotel-room search; an exit ban.

What is **very unlikely**: detention.

Spend your effort on the certainties — they are cheap to defeat (don't bring
the asset). Treat the unlikely-but-severe items with a *plan* rather than
constant anxiety. That is the whole strategy.

---

## 3. Legal landscape

### 3.1 The laws that shape this trip

- **Counter-Espionage Law** (revised, effective 1 Jul 2023). Expands
  "espionage" to include obtaining "documents, data, materials, or items
  related to national security and interests" — and does not define those
  terms. It explicitly authorizes security authorities to **inspect baggage
  and electronic devices**. The practical takeaway: the law is broad enough
  that the safest position is to carry nothing technical and nothing that
  documents infrastructure.
- **Data Security Law / Personal Information Protection Law.** Treats data as
  a national-security category; restricts cross-border data transfer. Relevant
  if you were to handle or move company/customer data while in-country — so
  don't.
- **Surveying and mapping rules.** China tightly controls geospatial data and
  unauthorized surveying/mapping by foreigners. Your company's domain
  intersects this. Carry no maps of, or data about, Chinese sites; do no
  "casual" mapping or drone-adjacent activity.
- **Encryption import rules.** China formally restricts importing unapproved
  encryption products. In practice, ordinary personal-device full-disk
  encryption is tolerated and not enforced against travelers — but it is one
  more reason to keep devices minimal and powered off at the border.

### 3.2 Border search authority

Customs and border officers may inspect devices **without a warrant or
individualized suspicion**. You can decline — but declining can mean you don't
enter, and refusal itself draws attention. The realistic posture is: assume a
search is possible, and make a search *boring* by carrying a near-empty burner.

### 3.3 Exit bans — the real shape of the risk

Exit bans prevent a person from leaving China. They matter to you, so
understand them precisely rather than vaguely:

- **Scale:** an estimated 30–40 US citizens were unable to leave China as of
  2024 (Dui Hua Foundation; likely an undercount). Small in absolute terms.
- **Who is actually hit:** people with a *nexus to a dispute in China* —
  unpaid debts, contract litigation, a company under investigation, regulatory
  matters, or use as diplomatic leverage. Legal representatives and general
  managers in finance/tech/manufacturing make up a large majority of foreign
  cases. The 2025 Wells Fargo banker case (which led Wells Fargo to suspend
  China travel) and the blocked USPTO employee case fit this pattern.
- **Your actual exposure:** **low.** You are visiting for a conference, with —
  assuming this is true — no Chinese subsidiary, no Chinese contracts in
  dispute, no Chinese investors, no local employment, no unpaid local debts.
  Exit bans are not random; they attach to a nexus. Your job is to **not
  create one**: don't sign anything, don't enter into local agreements, don't
  take on local obligations, don't get drawn into a "quick favor" involving a
  Chinese company.
- **How they surface:** without warning, usually discovered at the airport.
- **Why they are diplomatically sticky:** an exit ban with you physically free
  doesn't meet the US definition of "wrongful detention," which makes them
  harder to resolve than an outright detention.
- **Aggravating factor:** holding any Chinese identity or travel document
  impedes US consular help. Travel on your US passport only.

### 3.4 Detention and consular reality

Very unlikely for this trip. But the plan if it ever happened: stay calm; do
not sign documents you cannot read or do not understand; **request consular
access** and ask that the US Embassy be notified; say little until you have
consular contact. This is why §10's check-in plan and the paper copy of
embassy numbers exist.

### 3.5 VPNs

Legal gray area. Only government-approved VPNs are technically lawful, but no
foreign traveler has been prosecuted for ordinary personal VPN use. Treat a
VPN as a tool to *reach blocked services*, not as confidentiality against a
state adversary on its own network. See §8.3 for what actually works in 2026.

---

## 4. Devices

### 4.1 Asset decision matrix

| Asset | Bring it? | State it should be in |
|---|---|---|
| Primary phone | **No** | Backed up, powered off, secured at home. |
| Primary laptop | **No** | Same. |
| Burner phone | **Yes** | US-bought, clean, pre-provisioned (§4.3). |
| Laptop | **Avoid; only if essential** | Clean loaner, dumb terminal (§4.5). |
| Smartwatch / fitness tracker / earbuds | **No** | They pair, sync, and add attack surface for no benefit. |
| USB drives, hardware keys, external disks | **No** | Nothing to plug in, nothing to confiscate. |
| Work badge / RFID access cards | **No** | Leave all corporate physical credentials home. |

### 4.2 Primary devices — leave them home, correctly

- Take a **full encrypted backup** of phone and laptop before departure.
- If you use iCloud Backup, turn on **Advanced Data Protection** (ADP) on your
  real Apple ID — it end-to-end encrypts most iCloud categories so the backup
  itself isn't a soft target. (ADP is available on US Apple IDs.)
- **Power the devices off** and store them physically secure at home — not in
  checked luggage, not in an unattended office.
- Do not bring them "as a backup." There is no backup scenario that justifies
  carrying your entire digital life into the threat environment.

### 4.3 The burner phone — why US-bought, why iPhone

**Buy it in the US, not China.** A mainland-purchased phone is hostile on day
one: Chinese-market OEM firmware ships persistent telemetry (IMEI, MAC, GPS,
contacts, call/SMS history) that keeps transmitting even with opt-outs off; it
has no clean Google services; 2026 firmware-level malware ("Keenadu") was
found pre-installed and was specifically designed to activate on devices set
to a Chinese locale and lacking Google Play. And buying a phone/SIM in China
requires passport real-name registration anyway — it isn't even anonymous.

**Choose an iPhone, and here is the forensic reason.** An iPhone has two lock
states that matter:

- **AFU — After First Unlock:** once you've entered the passcode after boot,
  the encryption keys are in memory. Forensic tools (Cellebrite, GrayKey-class)
  can extract a large share of the filesystem in this state — reports put it
  near 95%.
- **BFU — Before First Unlock:** after a reboot, before the passcode has been
  entered even once, user data keys are *not* in memory. Forensic extraction
  in BFU yields essentially nothing of value — metadata, system logs, cached
  thumbnails — **no encrypted user files**.

A **powered-off iPhone boots into BFU.** On modern iOS, GrayKey-class tools
have only *partial* success against current versions even given time. And
iOS 18 added an **inactivity reboot**: a locked iPhone automatically reboots
after roughly 72 hours, dropping any seized device from AFU back to BFU on its
own. This is why "iPhone, powered fully off at the border, strong passcode" is
not folklore — it is the configuration that makes a device search produce
nothing.

A cheap current iPhone (an iPhone SE-class device) is enough. A clean Pixel is
an acceptable Android alternative but does not give you Lockdown Mode or the
same BFU story.

### 4.4 iOS hardening — the burner build

Configure all of this **before you fly**, on a clean home network:

- **Fresh Apple ID.** Create a new one with a new email address that does not
  contain your name and is not your primary address. Do not sign into your
  real iCloud. Do not join Family Sharing.
- **Strong alphanumeric passcode.** Settings → Face ID & Passcode → Change
  Passcode → Passcode Options → **Custom Alphanumeric Code**. Use 10+ random
  characters. A 6-digit PIN is brute-forceable; a long alphanumeric passcode
  is the thing BFU encryption actually rests on.
- **Biometrics: off for the border.** Face ID/Touch ID can be compelled with a
  look or a thumb; a passcode you choose when to enter. Either disable
  biometrics entirely, or know the quick-disable gesture and use it before
  every border interaction. A powered-off phone already requires the passcode.
- **Lockdown Mode on.** Settings → Privacy & Security → Lockdown Mode. It
  removes large classes of attack surface at a small usability cost — correct
  trade for a burner.
- **USB Restricted Mode on.** Confirm "Allow Access When Locked → Accessories"
  is **off**, so the data port is dead while the phone is locked.
- **Auto-updates / latest iOS.** Update to the current iOS before travel;
  patch level is part of the BFU story.
- **iCloud minimal or off** on the burner. If you use it at all, turn on ADP
  for the burner's account too. Nothing sensitive should exist to sync.
- **Record the IMEI and serial number** and keep them at home — cheap way to
  detect a hardware swap.

### 4.5 Laptop and remote-access architecture

Best answer: **don't bring a laptop.** Most conferences don't require one.

If you genuinely must work:

- Bring a **clean loaner** — fresh OS install, no company data, no client
  files, no source code, no cached credentials, no SSH keys, no saved VPN
  profiles to corporate.
- Treat it as a **dumb terminal**: do all real work inside a **remote desktop
  / VDI session** to a machine in the US. Nothing is stored locally; when the
  session closes, the laptop holds nothing.
- The remote machine should sit behind **conditional access** that you can
  revoke instantly, and ideally a separate account from your normal one.
- Full-disk encryption on; **power the laptop fully off** at the border (same
  at-rest reasoning as the phone).
- Assume that anything typed or displayed in a session conducted from a
  Chinese network is observable. Do not open your most sensitive material at
  all while in-country.

---

## 5. Border crossing

### 5.1 What actually happens at entry

- **Biometrics are mandatory and unavoidable.** As of late 2025, foreign
  nationals aged 14–70 provide **ten fingerprints and a facial image** at
  self-service kiosks at all ports of entry; twelve major entry points run
  facial-recognition "smart customs" lanes. You cannot decline this and still
  enter. Accept it — and internalize the implication: **your fingerprints and
  face are now in PRC systems permanently.** This is one more reason to use a
  passcode, not biometrics, to protect the burner — your biometrics are no
  longer a secret to this adversary.
- **Device checks.** Customs at major airports (Shenzhen, Shanghai and others)
  conduct **random** phone/laptop checks. iPhones may be connected to a
  diagnostic station; Android phones may have an app installed.
- **Keep the Android border-app threat in proportion.** The notorious
  data-stealing app — **BXAQ / "Fengcai"** — collects contacts, SMS, call
  logs, calendar, device info and installed-app lists, scans the device
  against ~73,000 specific files, and uploads results unencrypted to a police
  server. But it is documented overwhelmingly at **Xinjiang land borders**
  (e.g., the Kyrgyzstan crossing), installed on Android devices and usually
  removed before the phone is returned. It is **not** the standard experience
  at Beijing/Shanghai/Shenzhen airports. The capability and precedent exist,
  so plan as if any device could be touched — but don't mistake a land-border
  phenomenon for a universal airport one.

### 5.2 The powered-off doctrine

Power **every** device fully off before you land. Reasoning, made explicit:

- Off → boots to **BFU** → encryption keys not in memory → a search produces
  metadata, not your files.
- Off → the **passcode is required**, biometrics are inert until it's entered.
- A merely-locked (AFU) device is the weak state — that's the one extraction
  tools are good against.

### 5.3 Playbook — an officer asks to inspect or unlock a device

- **Comply with lawful instructions. Do not lie to an official.** Deception or
  argument converts a routine search into a serious problem.
- If you must unlock, **enter the passcode yourself**; don't hand it over
  verbally if avoidable.
- Stay calm, polite, brief. Answer what's asked; don't volunteer.
- This is exactly why the burner is near-empty: a search of it is boring and
  ends quickly.

### 5.4 Playbook — a device leaves your sight

- The moment a device is taken out of view, imaged, or has anything installed,
  treat it as **fully compromised** — permanently.
- Keep using it as a burner for the rest of the trip if you must, but enter no
  new credentials on it, and **retire it** on return (§12).
- It is cheap precisely so this outcome costs you nothing.

### 5.5 Concrete "do not carry" list

Across the border, on any device or in any bag: **no** penetration-testing
tools, exploit code, security scripts, or red-team material; **no** source
code or repositories; **no** customer lists, contracts, pricing, or roadmaps;
**no** site surveys, drone logs, inspection imagery, or infrastructure
documentation; **no** maps or geospatial data of Chinese locations; **no**
corporate credentials, SSH keys, or VPN-to-corp profiles; **no** sensitive
personal documents beyond the passport and visa you need.

---

## 6. Accounts, credentials, and 2FA

- **Dedicated travel email**, created for this trip. Do not sign into your
  primary Google/Apple/Microsoft, GitHub, company SSO, cloud storage, or your
  main password-manager vault on any device entering China.
- **2FA discipline.** If the burner holds the authenticator for your important
  accounts and the burner is seized, those accounts are exposed. Keep
  critical-account 2FA **off** the burner. Pre-stage only the minimum 2FA you
  genuinely need in-country, on accounts you could lose without consequence.
- A hardware security key can simply be confiscated — don't carry your real
  ones and don't treat one as guaranteed.
- If you use a password manager at all on the burner, it should be a
  **separate, near-empty vault** — not your real one.
- **Assume everything you access from China is observed.** Don't touch company
  internal systems except via the §4.5 remote-desktop path, and not even then
  for your most sensitive material.

---

## 7. Payments — Alipay yes, WeChat no

### 7.1 WeChat — don't install it

You need WeChat only for a conference ticket, and you can photograph the
ticket. So skip the app entirely:

- WeChat is **not end-to-end encrypted** — it uses Tencent's proprietary MMTLS;
  Tencent can read message content and is legally obliged to provide data to
  the state.
- Citizen Lab has documented **pervasive content surveillance** — messages,
  documents, and images scanned and hashed against sensitive-content
  blacklists, including in conversations among non-China-registered accounts.
- On install it harvests contacts, location, and device identifiers.

**Action:** before the trip, obtain the conference ticket as a **static
QR/barcode image** — screenshot it, have the organizer email the QR, or print
it. Confirm with the organizer that the gate code is static (nearly all are);
a photo scans fine. Only if the conference *mandates* the live WeChat app for
entry should you install it — and then on the **burner only**, a fresh clean
account, used for nothing but the ticket, deleted after.

### 7.2 Alipay — fine, with discipline

- Install Alipay **on the burner only**. Real-name verification ties the
  account to your **passport** — unavoidable; accept that one linkage and keep
  everything else minimal.
- Fund it with an **international card** (Visa/Mastercard now work) or use the
  **TourCard** prepaid product for short visits.
- For a short trip, **cash plus a low-limit card** keeps the smallest
  footprint; treat Alipay as the convenient backup, not the default.
- Do **not** import contacts. Do **not** link your primary phone number or
  email. Keep transaction values modest — ID-registration thresholds kick in
  around US$500 per transaction and US$2,000 per year.
- Delete the app and clear the account associations after the trip.

---

## 8. Networks and connectivity

### 8.1 Assume interception, always

Every network in China is built for lawful intercept. Hotel Wi-Fi, conference
Wi-Fi, and café hotspots are the *most* exposed — possibly running TLS
interception or capturing credentials outright. Default rules:

- **No public Wi-Fi.** Use cellular data or your own hotspot.
- Assume calls, SMS, and any messaging are monitored. Genuinely sensitive
  conversations don't happen in China — not on a "better app," not at all.

### 8.2 SIM / eSIM

Prefer a **foreign roaming eSIM or travel SIM from a non-Chinese carrier**
over a Chinese SIM. A Chinese SIM requires real-name registration and routes
entirely through domestic infrastructure; foreign roaming sometimes tunnels
traffic out via the home carrier and often reaches the open internet without a
VPN. Either way, assume monitoring — the roaming choice is about reducing
identity linkage and improving reach, not about confidentiality.

### 8.3 VPN — what actually works in 2026

The landscape changed sharply. In **April 2026 ("the Great Unplug")** China
physically disconnected relay infrastructure for Shadowsocks-, V2Ray-, and
Trojan-based proxies. The Great Firewall now uses **active probing** (it
connects to suspected servers and blacklists ones that don't behave like
normal web servers, often within hours) and **ML traffic classifiers** that
flag flows by timing and bidirectional patterns. Shadowsocks has a
high-entropy first-packet fingerprint; V2Ray's VMess has recognizable
handshakes — both are increasingly unreliable.

What survived: commercial VPNs using **direct overseas connections with native
TLS 1.3 obfuscation** (Astrill and ExpressVPN were specifically named as still
working after the crackdown).

Practical guidance:

- Choose a reputable commercial VPN with **TLS-1.3-based obfuscation**, and
  **install and test it before you arrive** — VPN provider sites and app
  stores are blocked once you're inside.
- Install **two** different providers as fallback; expect intermittent
  failure regardless.
- A VPN is for *reaching blocked services* (your email, maps, etc.). It is
  **not** confidentiality against this adversary on its own network. Don't let
  a connected VPN icon create false confidence.

### 8.4 Pre-load to reduce your need to connect

Before departure, download **offline maps**, an **offline translation pack**,
and your **conference ticket image** onto the burner. Every offline asset is
one less reason to touch a hostile network.

---

## 9. Physical security and the hotel

- **Never leave a device unattended** — not in the room, not in the room safe.
  Assume hotel rooms and safes can be accessed by a motivated party. Carry
  devices on you. (A targeted room search is unlikely for a routine conference
  visitor — but the mitigation is free, so just do it.)
- **No unknown USB or chargers.** Don't use hotel/airport/conference USB
  ports (juice-jacking). Use **your own charger into a wall outlet**, ideally
  with a **USB data blocker**, or charge from **your own power bank**.
- **Refuse gifted electronics** — USB drives, "promotional" gadgets, cables,
  even at the conference. Accept-and-discard if refusing would be awkward;
  never connect them.
- **Social engineering and honeypots.** A new acquaintance who is unusually
  interested in your technology, customers, or sites is collecting. Keep all
  answers at the level of your public website; redirect; don't be drawn into
  "off the record."
- **IMSI-catchers** may operate near venues; it is one more reason cellular is
  for reach, not for sensitive content.
- If you ever must leave a device behind, use tamper-evidence (a hair across a
  seam, a photo of exact placement) — and still assume it was accessed.

---

## 10. Communications and check-in plan

Set this up before you fly. It is normal travel safety, nothing exotic:

- **A trusted contact at home** (and ideally one at your company) holds your
  full itinerary: flights, hotel, conference dates, and expected departure.
- **A check-in cadence** — e.g., a short message at a set time each day. Agree
  in advance what "I'm fine" looks like and that *silence past a window* is
  the trigger.
- **An escalation plan if a check-in is missed:** the contact tries your
  burner, then the hotel, then contacts the **US Embassy/Consulate** and your
  company's legal/security point of contact.
- **Carry embassy and consulate phone numbers on paper.** Devices fail, get
  searched, or run flat.
- Keep the plan **simple and ordinary-looking** — it is just a worried
  founder's travel safety routine, which is exactly what it is.
- Brief whoever covers for you at the company on what to do if you can't be
  reached, including revoking your remote-access conditional-access grant.

---

## 11. The conference itself

- **Badge / registration:** give the minimum required. Assume the attendee
  list and any app are data-collection surfaces.
- **The ticket:** static QR image on the burner (see §7.1).
- **Swag and USB handouts:** never plug in conference USB drives or "free"
  cables. Decline or discard.
- **Demos and shared machines:** don't log into anything on a demo kiosk or a
  borrowed laptop. Don't plug your burner into demo equipment.
- **Networking conversations:** public-website-level detail only. Be
  especially careful with specifics about *which* data centers or substations
  you inspect, customer names, deployment scale, and anything about how your
  drones or models work. "We do AI-assisted infrastructure inspection" is
  plenty.
- **Photos:** be mindful of what's in the background of photos you take or
  appear in; avoid photographing anything that looks like sensitive
  infrastructure.
- **Presenting?** Have your slides reviewed beforehand so nothing sensitive is
  on them, and present from conference equipment or the dumb-terminal laptop —
  not from anything that matters.

---

## 12. Returning home — assume-compromise protocol

Compromise usually surfaces *after* the trip. Close it out methodically:

1. **Do not reconnect** the burner — or any device that entered China — to
   your home or corporate network. Ever.
2. **Retire the burner phone.** Factory reset it; for a device that was
   searched, imaged, or had anything installed, physically retire it. Never
   reuse it for anything sensitive.
3. **Rotate credentials**, in priority order: (a) anything used or reachable
   from the burner, (b) the travel email, (c) any account whose 2FA was on the
   burner. Change passwords *and* re-issue 2FA.
4. **Revoke** the remote-access conditional-access grant and the loaner
   laptop's sessions.
5. **Wipe the loaner laptop** to a fresh OS install before it touches anything
   else.
6. **Watch for follow-on phishing** for several weeks — targeted
   spear-phishing is a common second stage after a trip.
7. Your **primary phone never left the US**, so it is clean — just make sure
   nothing from the trip (no burner backup, no transferred files) is restored
   onto it.

---

## 13. Founder / Jinki-AI specifics

- **Your sector is the sensitive part.** Drone operations, critical-
  infrastructure inspection, and geospatial/mapping data all sit inside areas
  China regulates as national-security relevant. Carry **zero** technical
  materials, customer lists, site surveys, drone logs, inspection imagery, or
  IP across the border.
- **Guard conversations.** At a conference, a friendly technical question
  about your pipeline, your customers, or specific sites is information
  collection. Public-website level, always.
- **As a security consultant:** absolutely no pentest tools, exploit code, or
  security tooling on any device that crosses the border. This is the highest
  legal-risk item you control completely.
- **Don't create an exit-ban nexus** (§3.3): sign nothing, enter no local
  agreements, take on no local obligations, accept no "quick favor" wrapped
  around a Chinese company. Your exit-ban risk is low *because* you have no
  nexus — keep it that way.
- **Company-side:** make sure someone can revoke your access and cover your
  responsibilities, and that legal/security knows your dates.

---

## 14. Calibrated risk register

For a short conference trip, no local legal entanglement, following this guide:

| Threat | Likelihood | Impact if it happens | Primary mitigation |
|---|---|---|---|
| Network interception (hotel/conference Wi-Fi) | **Near-certain** | Low — nothing sensitive in transit | No public Wi-Fi; cellular; nothing sensitive done in-country |
| Biometric capture at entry | **Certain** | Low — unavoidable, expected | Accept it; use passcode not biometrics on the burner |
| WeChat/Alipay data harvest | **Certain if installed** | Low–Moderate | Don't install WeChat; keep Alipay minimal & burner-only |
| Malware on a China-bought phone | **High if you buy one** | High | Don't — US-bought clean burner instead |
| Random border device check | **Moderate** | Low — burner is near-empty | Powered-off iPhone, strong passcode, nothing technical |
| Full device imaging at customs | **Low–Moderate** | Low — BFU yields little | Power off; minimal contents |
| Android border-app install | **Low at airports** | Moderate — treat device as lost | Burner is disposable; retire on return |
| Carrying prohibited technical material | **Only if you fail to prep** | **Severe** (legal) | The §5.5 do-not-carry list — fully in your control |
| Hotel-room access to an unattended device | **Low** | Moderate | Never leave devices unattended |
| Industrial-espionage interest | **Low–Moderate** | Moderate | Carry no IP; guard conversations |
| Exit ban | **Low** | Severe | No local nexus; check-in plan; travel on US passport only |
| Detention | **Very low** | Severe | Check-in plan; consular numbers on paper |
| Follow-on phishing after return | **Moderate** | Moderate | Assume-compromise protocol; rotate credentials; vigilance |

The pattern: the **certain** threats are all **low-impact** once you don't
bring the asset. The **severe** threats are all **low-likelihood** *and*
largely within your control. That is a winnable position — which is the point
of doing the prep.

---

## 15. Checklists

### Pre-trip (at home, clean network)
- [ ] Read the current US State Dept China advisory; enroll in STEP.
- [ ] Confirm no Chinese-entity dispute/contract/investment nexus; consult counsel if any.
- [ ] Full **encrypted backup** of primary phone + laptop; enable ADP.
- [ ] Power off primary devices; store them physically secure at home.
- [ ] Buy a cheap clean burner phone **in the US** (iPhone SE-class).
- [ ] Provision the burner per Appendix A.
- [ ] Create a dedicated **travel email**; keep primary-account 2FA off the burner.
- [ ] Get the conference ticket as a **static QR/barcode image**. Do not install WeChat.
- [ ] Install Alipay on the burner; link an international card or TourCard.
- [ ] Install + test **two** TLS-1.3-obfuscated VPNs before departure.
- [ ] Arrange a foreign roaming eSIM/SIM.
- [ ] Download offline maps + offline translation pack.
- [ ] Pack a personal charger, **USB data blocker**, and power bank.
- [ ] Leave smartwatch, hardware keys, USB drives, work badge at home.
- [ ] Set up the §10 check-in plan; carry embassy numbers **on paper**.
- [ ] If bringing a laptop: clean loaner + remote-desktop/VDI configured.

### At the border
- [ ] All devices **powered fully off** before landing.
- [ ] Biometrics off on the burner; passcode required.
- [ ] Nothing technical, no client data, no site material on you (§5.5).
- [ ] Expect mandatory fingerprint + facial capture; that's normal.
- [ ] If searched: comply, calm, brief, **do not lie to officials**; enter the passcode yourself.
- [ ] Flag any device taken out of sight as compromised.
- [ ] Travel on your **US passport only**.

### In-country
- [ ] Devices never left unattended (not in the room, not in the safe).
- [ ] No public Wi-Fi; cellular or own hotspot only.
- [ ] No unknown USB/chargers; own charger + data blocker / power bank only.
- [ ] No login to primary or company accounts; remote desktop only, sparingly.
- [ ] No sensitive conversations anywhere; public-website-level detail only.
- [ ] Refuse gifted electronics and conference USB swag.
- [ ] Sign nothing; take on no local obligations.
- [ ] Daily check-in on schedule.

### Returning home
- [ ] Do **not** reconnect the burner to home/corporate networks.
- [ ] Factory reset and **retire** the burner phone.
- [ ] Rotate passwords + 2FA: burner-reachable accounts → travel email → 2FA-on-burner accounts.
- [ ] Revoke remote-access grant; wipe the loaner laptop.
- [ ] Watch for phishing for several weeks.
- [ ] Restore nothing from the trip onto your primary phone.

---

## Appendix A — Burner iPhone build, step by step

Do all of this at home, on a network you trust, before departure.

1. Buy a cheap current iPhone (iPhone SE-class) in the US. Payment method is
   irrelevant — your adversary here is not the US.
2. On first setup, **create a brand-new Apple ID** with a fresh email that
   does not contain your name. Do not sign into your real iCloud. Do not join
   Family Sharing.
3. Update to the **latest iOS**.
4. Settings → Face ID & Passcode → Change Passcode → Passcode Options →
   **Custom Alphanumeric Code** → set **10+ random characters**.
5. **Disable Face ID/Touch ID** for unlock (or learn the quick-disable gesture
   and commit to using it at every border touchpoint).
6. Settings → Privacy & Security → **Lockdown Mode** → On.
7. Face ID & Passcode → confirm **"Allow Access When Locked → Accessories" is
   Off** (USB Restricted Mode).
8. Keep **iCloud minimal or off**. If used at all, enable **Advanced Data
   Protection** on the burner's account.
9. Install only what you need: **Alipay**; an **offline-capable maps** app
   with the maps pre-downloaded; an **offline translation** app with the
   language pack; **two** TLS-1.3-obfuscated **VPNs**; a ride-hailing app if
   needed. Save the **conference QR ticket** into Photos.
10. Add **zero** real contacts. Memorize the few numbers you truly need, or
    store an absolute minimum.
11. **Test both VPNs** and the offline assets before you leave.
12. Record the **IMEI and serial number**; leave that note at home.
13. Just before the border: **power the phone fully off.**
14. After return: factory reset and **retire** it (§12).

## Appendix B — Fast decision rules

- **Officer asks to unlock a device** → comply, stay calm, enter the passcode
  yourself, don't argue, don't lie.
- **Officer wants to install an app / take the device away** → comply if it's
  required to enter; treat the device as compromised; it's a burner, so the
  cost is zero.
- **Device leaves your sight** → compromised. No new credentials on it; retire
  on return.
- **Free Wi-Fi offered** → decline; use cellular.
- **Handed a USB drive or cable** → never plug it in; accept-and-discard or
  decline.
- **New contact gets very interested in your tech/customers/sites** →
  public-website level only; redirect; don't go "off the record."
- **Asked to sign something, or join a local arrangement** → don't; "I'll have
  to consult counsel."
- **You miss a check-in** → your home contact escalates per §10.
- **Told at the airport you can't leave** → stay calm; contact the US Embassy
  immediately; contact company legal; **request consular access**; do not sign
  documents you don't fully understand.

---

*Bottom line, restated for the deep edition: the threats that are certain are
all cheap to defeat — you defeat them by not bringing the asset. The threats
that are severe are all low-probability and mostly within your control — you
manage them with preparation and a plan, not anxiety. Leave the real devices
home, carry a clean US-bought iPhone with nothing technical on it, power it off
at the border, skip WeChat, keep Alipay minimal, treat every network as
hostile, keep a check-in plan, and create no local entanglements. Do that and
a worst-case device loss costs you a cheap phone and an afternoon of credential
rotation — nothing more.*
