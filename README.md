# FRITZ!Fon Call Alert for Home Assistant

Home Assistant custom integration that listens for incoming calls on the FRITZ!Box call monitor and provides a binary sensor, a `fritzfon_call` event, and an optional full-screen Lovelace alert card.

## Install

Copy `custom_components/fritzfon` into Home Assistant's `custom_components` directory, restart Home Assistant, then add **FRITZ!Fon Call Alert** under **Settings → Devices & services → Add integration**. Enter the FRITZ!Box hostname or IP and credentials for a FRITZ!Box user allowed to access telephony and its phonebook.

Before setup, enable the FRITZ!Box call monitor by dialing `#96*5*` from a phone connected directly to the box. Enable **Permit access for applications** under **Home Network → Network → Network Settings**. Allow Home Assistant to reach TCP port `1012` (call monitor) and TCP port `49000` (TR-064 phonebook) on the FRITZ!Box. The integration downloads the first available phonebook during setup and resolves the caller name locally.

## Full-screen kiosk alert

Add a **Manual** dashboard card with:

```yaml
type: custom:fritzfon-call-card
```

The card opens a full-screen overlay on `ringing` and can be dismissed on screen. It listens to the `fritzfon_call` Home Assistant event. The integration also creates a binary sensor whose attributes include `from`, `to`, and `call_id`.

Example automation:

```yaml
automation:
  - alias: "Incoming FRITZ!Box call"
    triggers:
      - trigger: event
        event_type: fritzfon_call
        event_data:
          state: ringing
    actions:
      - action: notify.mobile_app_phone
        data:
          title: "Eingehender Anruf"
          message: "{{ trigger.event.data.from }}"
```

## Scope

This version detects and displays calls. It does not register a SIP handset, carry call audio, or answer calls. A real SIP endpoint requires its own telephony device/account configured in the FRITZ!Box and a SIP media client; FRITZ!Box credentials alone do not create a phone endpoint.
