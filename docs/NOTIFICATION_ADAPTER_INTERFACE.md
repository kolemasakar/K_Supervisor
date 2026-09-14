# NOTIFICATION_ADAPTER_INTERFACE
Майбутня transport-neutral межа для notification adapters поверх чинної email-first політики.

Version: 1.0
Status: DESIGN BASELINE
Baseline Phase: 16

## 1. Current State

The implemented notification channel remains EMAIL. `NotificationEvent` is transport-neutral at the workflow/control-plane level, while `NotificationBroker` currently accepts only `NotificationChannel.EMAIL` and sends through the Phase 3 `EmailProvider` boundary.

This document defines how future transports should integrate. It does not claim WhatsApp, Viber, SMS or social transports are implemented.

## 2. Adapter Responsibility

A future transport adapter should implement a narrow send boundary equivalent to:

```text
send(message, idempotency_key) -> provider_message_id | None
```

The adapter owns provider-specific request formatting, connectivity and provider response parsing. The Notification Broker owns delivery policy, delivery-attempt state, duplicate suppression and project correlation.

## 3. Required Semantics

A compliant notification adapter must:

- accept an explicit idempotency key;
- return a provider message identifier when available;
- raise/return a normalized failure without changing Project state directly;
- never persist raw credentials in NotificationEvent or delivery records;
- resolve credentials only through protected access references/backends;
- avoid hidden retries that bypass platform delivery-attempt accounting;
- preserve project_id, notification_id and human_action_id correlation;
- not treat successful transport delivery as completion of the owner action.

## 4. Future Discovery

A future transport implementation may be distributed through the Phase 16 `k_supervisor.adapters` entry-point group. The extension registrar should request the host registry/service it needs from `ExtensionContext` rather than modifying Supervisor or Notification Broker source.

When more than EMAIL becomes executable, `NotificationChannel`, transport selection policy and channel-specific validation must be versioned deliberately rather than silently accepting arbitrary strings.

## 5. Security Boundary

Messages must not contain raw secrets. Transport credentials must remain behind SecretBackend/AccessReference boundaries. Logs and normalized audit records should contain correlation IDs, status and provider message IDs where safe, not authentication material or full private message content by default.

## 6. Owner-Control Boundary

`SENT` means only that the transport accepted or delivered the notification according to the adapter contract. HumanActionRequest verification remains the authoritative signal that an owner-required action is complete and that a project may resume.
