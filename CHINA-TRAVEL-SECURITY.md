# China Travel Security Advisory

**Audience:** A cybersecurity consultant and startup founder (Jinki AI / BAHB —
autonomous drone inspection AI for data centers and substations) traveling to
mainland China for a conference. Threat tolerance: paranoid. Good — for this
trip, paranoid is the correct setting.

---

## 0. Disclaimer

This is operational-security guidance, **not legal advice**. Laws and
enforcement in China change quickly and are applied unevenly. Before you go:

- Read the **current US State Department China Travel Advisory** in full
  (the level and the specific warnings change — do not rely on a remembered
  version).
- Enroll in **STEP** (Smart Traveler Enrollment Program) so the embassy can
  reach you.
- If you carry anything that could be sensitive, or you have any business
  dispute with a Chinese entity, talk to **counsel** before flying.

---

## 1. The short version

Your instinct is half right. Scored against research:

| Your idea | Verdict | What to do instead |
|---|---|---|
| Back up + leave your real phone in the US | **Correct** | Keep it. Encrypted backup, power off, store securely at home. |
| Buy the phone *in China* | **Risky** | Buy a clean burner **in the US** and pre-provision it before you fly. |
| Log into WeChat | **Avoidable** | Don't install WeChat. Carry the conference ticket as a static QR image. |
| Log into Alipay | **OK, with care** | Burner-only, international card or TourCard, minimal footprint. |

Everything below is the reasoning and the detail.

---

## 2. Threat model — who you are defending against

You are not defending against one adversary. You are defending against four,
and they overlap:

1. **The state (MSS / customs / network operators).** Since the revised
   Counter-Espionage Law (effective 1 Jul 2023) and 2025 national-security
   rules, border officers may inspect baggage and electronic devices
   **without a warrant**. Customs at Shenzhen and Shanghai already do random
   phone/laptop checks; iPhones get connected to diagnostic stations, Android
   phones can have a data-collection app installed. All domestic networks are
   lawful-intercept by design.

2. **Industrial / competitive espionage.** Your company does drone-based
   inspection of **critical infrastructure** (data centers, substations) and
   handles geospatial/mapping data. That is a sensitive sector. Assume a
   commercial interest in your IP, customer list, and site data.

3. **Network interception.** Hotel Wi-Fi, conference Wi-Fi, public hotspots —
   treat every network as monitored and possibly hostile.

4. **Opportunistic crime.** Device theft, juice-jacking, malicious chargers.

**Why you are elevated-risk specifically:** The Counter-Espionage Law defines
espionage as handling "documents, data, materials, or items related to
national security and interests" — and *none of those terms is defined*. A
security consultant carrying tooling, or a critical-infrastructure founder
carrying site/mapping data, is exactly the ambiguous profile that law was
written broadly enough to reach. The safe assumption: **anything technical you
carry can be reframed as a problem.** So carry nothing technical.

The core mental model for the whole trip:

> Every device you bring will be searched. Every network will be monitored.
> Every device left unattended will be accessed. Plan as if all three already
> happened.

---

## 3. Devices

### 3.1 Leave your real phone and laptop in the US

This part of your plan is right. Before you go:

- Take a **full encrypted backup** of your primary phone (and laptop).
- **Power the devices off** and store them somewhere secure at home — not in
  checked luggage, not in an office someone else can access.
- Do **not** bring them "just in case." A device that never enters China
  cannot be compromised in China.

### 3.2 The burner phone — buy it in the US, not in China

You proposed buying a phone in China. Don't. A phone bought on the mainland is
a **hostile device the moment you buy it**:

- Chinese-market OEM firmware (Xiaomi/Redmi, etc.) ships **persistent
  telemetry** — IMEI, MAC, GPS, contacts, call/SMS history — and keeps sending
  it even with the "send usage data" opt-outs turned off.
- These phones have **no clean Google services** and pull apps from OEM stores.
- In 2026, firmware-level malware ("Keenadu") was found pre-installed on
  devices and was specifically designed to activate on handsets set to a
  **Chinese locale/time zone and lacking Google Play** — i.e. exactly a
  phone bought in-country.
- Buying a phone and SIM in China requires **passport real-name registration**
  anyway, so it isn't even anonymous.

**Do this instead** — buy a cheap, clean phone in the US and provision it
before you fly:

- **Hardware:** an inexpensive **iPhone (e.g. iPhone SE)** is the better
  paranoid choice over a low-end Android — stronger default at-rest
  encryption, no OEM firmware fork, a hardened before-first-unlock state, and
  **Lockdown Mode**. A clean Pixel is acceptable if you prefer Android.
- **Account:** create a **fresh Apple ID / Google account** from a clean
  network, not linked to your real name, primary email, or company.
- **Passcode:** a **strong alphanumeric passcode** — not a 6-digit PIN, not
  biometric-only.
- **Lockdown Mode:** enable it (iOS). Enable **USB Restricted Mode** so the
  data port is blocked while locked.
- **Contents:** minimal apps, **zero** company data, **zero** real contacts,
  no documents, no corporate email/cloud/VPN-to-corp.
- After the trip this phone is **disposable** — see §9.

### 3.3 Laptop

Best option: **don't bring one.** A conference rarely requires it.

If you genuinely must:

- Bring a **clean loaner** — fresh OS install, no company data, no client
  files, no source code, no credentials cached.
- Do real work only via **remote desktop / VDI into a machine in the US**.
  Store nothing locally; the laptop is a dumb terminal.
- Full-disk encryption on. (Note: China technically restricts importing
  unapproved encryption products; in practice personal-device full-disk
  encryption is tolerated. Keep the laptop **powered off** at the border so
  it is encrypted-at-rest, not just locked.)

---

## 4. Border crossing

- **Power every device fully OFF before you land.** A powered-off phone boots
  into the *before-first-unlock* state: the strongest encryption state, and
  biometrics are disabled until the passcode is entered once. A merely-locked
  phone is weaker.
- **Biometrics off, passcode on.** A face/fingerprint can be compelled with a
  glance or a hand. A passcode you can choose to enter — and a powered-off
  device requires it.
- If officers search a device, **comply with lawful instructions and do not
  lie to officials.** Arguing or deceiving an officer escalates a search into
  a far worse problem.
- If a device is taken out of your sight, imaged, or has an app installed,
  treat it as **fully compromised** from that moment — quarantine and retire
  it after the trip (§9). This is the main reason the burner must be cheap.
- **Carry nothing technical that could be reframed.** No penetration-testing
  tools, no exploit code, no security tooling, no client data, no source code,
  no IP, no documentation of critical-infrastructure sites. For you, this is
  the single biggest *legal* risk of the trip — bigger than malware.

---

## 5. Accounts, credentials, and 2FA

- Use a **dedicated travel email** created for this trip. Do not sign into
  your primary Google/Apple/Microsoft, GitHub, company SSO, or your main
  password-manager vault on any device that enters China.
- **2FA is a trap if you over-pack it.** If the burner holds the authenticator
  for your important accounts and the burner is seized, those accounts are
  exposed. Keep critical-account 2FA **off** the burner. Pre-stage on the
  burner only the bare minimum you actually need in-country.
- A hardware security key can simply be confiscated — don't treat it as
  guaranteed protection.
- Assume **everything you access while in China is observed.** Do not log into
  company internal systems. If you must work, see §3.3 (remote desktop only).

---

## 6. Payments — Alipay yes, WeChat no

### 6.1 WeChat — skip it

You said WeChat is only needed for your conference ticket, and that you can
photograph the ticket. **Do that — and don't install WeChat at all.** Reasons:

- WeChat is **not end-to-end encrypted.** It uses Tencent's proprietary MMTLS;
  Tencent can decrypt and read messages, and is legally obliged to hand data
  to the state.
- Citizen Lab has documented **pervasive content surveillance** — messages,
  documents, and images are scanned and hashed against sensitive-content
  blacklists, including conversations among non-China accounts.
- The app harvests contacts, location, and device identifiers on install.

**Action:** before the trip, get the conference ticket as a **static QR/barcode
image** — screenshot it, have an organizer email the QR, or print it.
Confirm with the organizer that the gate QR is static (almost all are). A
photo scans fine at the gate. Only if the conference *mandates* the live
WeChat app should you install it — and then on the **burner only**, with a
clean account, used for nothing but the ticket.

### 6.2 Alipay — fine, with discipline

- Install Alipay **on the burner only.** Real-name verification ties the
  account to your **passport** — that is unavoidable and is the price of
  entry; accept it, and keep everything else minimal.
- Fund it with an **international card** (Visa/Mastercard now work) or use the
  **TourCard** prepaid option designed for short visits.
- For a short conference trip, **cash plus a low-limit card** keeps your
  digital footprint smallest; treat Alipay as the convenient backup.
- Do **not** import contacts. Do **not** link your primary phone number or
  email. Keep transaction values modest (ID registration kicks in around
  US$500/transaction and US$2,000/year).

---

## 7. Connectivity

- **SIM:** prefer a **foreign roaming eSIM / travel SIM from a non-Chinese
  carrier** over a Chinese SIM. A Chinese SIM requires real-name registration
  and routes entirely through domestic infrastructure; foreign roaming
  sometimes tunnels your traffic out through the home carrier. Either way,
  assume monitoring.
- **VPN:** legally a gray area. No foreign traveler has been prosecuted for
  personal VPN use, but the Great Firewall blocks many VPN protocols and the
  app stores — so **install a reputable, obfuscated VPN before you arrive.**
  Understand its limits: a VPN helps you *reach blocked services*; it is **not**
  meaningful confidentiality against a state adversary operating its own
  network. Don't let it create false confidence.
- **Avoid public Wi-Fi** — hotel, conference, café. Use cellular data or your
  own hotspot.
- **Comms:** Signal/WhatsApp are blocked without a VPN. For genuinely
  sensitive conversations, the answer is not "use a better app" — it is
  **don't have that conversation in China.** Assume calls, SMS, and any
  messaging are monitored.

---

## 8. Physical security and the hotel

- **Never leave a device unattended** — not in the room, not in the room safe.
  Assume hotel rooms and safes can be accessed. Carry your devices on you.
- **No unknown USB or chargers.** Don't plug into hotel/airport/conference USB
  ports (juice-jacking). Use your **own charger into a wall outlet**, ideally
  with a **USB data blocker**, or charge from your **own power bank**.
- **Refuse gifted electronics** — USB drives, "promotional" gadgets, cables.
- Be alert to **social engineering and honeypots.** Keep business
  conversations generic; assume new acquaintances may have a reason to be
  friendly.
- If you ever must leave a device behind, use tamper-evident measures (a
  hair, a photo of the exact placement) — and still assume it was accessed.

---

## 9. Returning home — the part people forget

Compromise often shows up *after* the trip. Close it out deliberately:

- **Do not reconnect the burner** — or any device that was in China — to your
  home or corporate network. Ever.
- **Factory reset and retire the burner phone.** It is cheap for this reason.
  Do not reuse it for anything sensitive. If a device was searched, imaged, or
  had an app installed at the border, physically retire it.
- **Rotate credentials** for every account that was reachable from the burner
  or that you used during the trip — passwords and 2FA.
- **Watch for follow-on phishing** for several weeks. Targeted spear-phishing
  after a trip is a common second stage.
- Your **primary phone never went to China**, so it is clean — just make sure
  nothing from the trip (no burner backup, no files) is restored onto it.

---

## 10. Founder / Jinki-AI–specific notes

- **Your sector is sensitive.** Drone operations, critical-infrastructure
  inspection (data centers, substations), and geospatial/mapping data all
  touch areas China treats as national-security relevant (mapping/surveying
  rules, the Data Security Law, the Counter-Espionage Law). Carry **zero**
  technical materials, customer lists, site surveys, drone logs, or IP.
- **Guard conference conversations.** A casual technical question about your
  inspection pipeline, customers, or sites is still information collection.
  Keep answers at the level of your public website.
- **As a security consultant:** absolutely no penetration-testing tools,
  exploit code, or security tooling on any device that crosses the border.
- **Exit bans exist.** The probability is low for a short conference trip with
  no local legal dispute — but be aware the mechanism exists, keep your
  itinerary tight, and make sure someone at home knows your schedule and has
  a check-in cadence.

---

## 11. Checklist

### Pre-trip (do at home, on a clean network)
- [ ] Read the current US State Dept China advisory; enroll in STEP.
- [ ] Full **encrypted backup** of primary phone + laptop.
- [ ] Power off primary devices; store them securely at home.
- [ ] Buy a cheap clean burner phone **in the US** (iPhone SE / clean Pixel).
- [ ] Provision the burner: fresh non-identifying Apple/Google ID, strong
      **alphanumeric passcode**, Lockdown Mode + USB Restricted Mode on,
      minimal apps, no company data/contacts/docs.
- [ ] Create a dedicated **travel email**; do not load primary-account 2FA.
- [ ] Get the conference ticket as a **static QR/barcode image** (no WeChat).
- [ ] Install Alipay on the burner; link an international card or TourCard.
- [ ] Install an obfuscated VPN on the burner **before** departure (if needed).
- [ ] Arrange a foreign roaming eSIM/SIM.
- [ ] Pack a personal charger, **USB data blocker**, and power bank.
- [ ] Tell someone at home your itinerary + a check-in schedule.

### At the border
- [ ] All devices **powered fully off** before landing.
- [ ] Biometrics off; passcode required.
- [ ] No pentest tools, client data, source code, IP, or site material on you.
- [ ] If searched: comply, stay calm, **do not lie to officials**.
- [ ] Mentally flag any device taken out of sight as compromised.

### In-country
- [ ] Devices **never** left unattended (not in the room, not in the safe).
- [ ] No public Wi-Fi; cellular or own hotspot only.
- [ ] No unknown USB/chargers; own charger + data blocker / power bank only.
- [ ] No login to primary or company accounts; work only via remote desktop.
- [ ] No sensitive conversations — assume everything is monitored.
- [ ] Refuse gifted electronics; keep business talk generic.

### Returning home
- [ ] Do **not** reconnect the burner to home/corporate networks.
- [ ] Factory reset and **retire** the burner phone.
- [ ] Rotate passwords + 2FA for every account used or reachable on the trip.
- [ ] Watch for phishing for several weeks.
- [ ] Restore nothing from the trip onto your primary phone.

---

*Bottom line: leave the real phone home (you had this right), bring a clean
US-bought burner instead of buying one in China, skip WeChat and photograph
the ticket, keep Alipay minimal, and treat every device and network in China
as already compromised. The discipline that matters most is the simplest:
carry nothing technical across the border.*
