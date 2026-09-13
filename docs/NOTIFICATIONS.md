# NOTIFICATIONS
Архітектура повідомлень власника, Human Intervention та email-first delivery baseline K_Supervisor.

Version: 1.0
Status: ACTIVE
Phase: 3

## 1. Scope

Phase 3 establishes the owner-control boundary for autonomous project work.

The initial notification transport is email only.

```text
Project / Workflow
      |
      v
HumanActionRequest / NotificationEvent
      |
      +--> HumanInterventionBroker
      |
      +--> NotificationBroker
                |
                v
           EmailProvider
                |
                v
          SMTP relay adapter
```

WhatsApp, Viber, and other messaging transports remain deferred extension points.

## 2. Human Intervention

`HumanInterventionBroker` manages work that requires owner action.

A blocking action moves only the affected project to:

```text
WAITING_FOR_OWNER
```

Other projects remain independent.

After the completion condition is verified and no other blocking owner actions remain, the affected project returns to:

```text
ACTIVE
```

Human action state and project operational state are persisted separately.

The action record and operational state transition are written atomically when both change together.

## 3. Human Action States

Baseline states:

```text
OPEN
NOTIFIED
WAITING_FOR_OWNER
VERIFYING
VERIFIED
CANCELLED
FAILED
```

`VERIFIED` requires `resolved_at`.

Verification is separate from message delivery.

```text
NOTIFICATION_SENT != OWNER_ACTION_VERIFIED
```

## 4. Notification Broker

`NotificationBroker` is transport-neutral from the caller perspective.

It accepts a structured `NotificationEvent` and uses an `EmailProvider` implementation for delivery.

Immediate email baseline:

```text
ACTION_REQUIRED
FIRST_WORKING_REACHED
RELEASE_READY
CRITICAL_FAILURE
```

An event with `action_required=true` is also delivered immediately.

Routine informational events may be persisted without immediate delivery.

## 5. Structured Email

The baseline email contains:

```text
project identifier
event type
severity
summary
required action when applicable
human action identifier when applicable
blocking flag
```

Notification messages must not contain raw passwords, API keys, tokens, recovery codes, or private keys.

## 6. Email Provider Contract

The transport contract is:

```text
EmailProvider.send(OutboundEmail, idempotency_key)
```

The platform core does not depend on SMTP implementation details.

The initial concrete transport is `SMTPRelayEmailProvider`.

This adapter is intended for an approved SMTP relay or equivalent infrastructure endpoint and does not persist credentials.

Authenticated provider integrations should use the future Secret Manager boundary rather than embedding credentials in repository configuration.

## 7. Owner Email Resolution

The owner destination belongs to project configuration / approved ProjectSpec policy.

`NotificationBroker` receives the resolved recipient at delivery time and does not own global user identity.

This preserves project isolation and allows different projects to use different owner or escalation destinations later.

## 8. Delivery Records

Every delivery attempt is represented by `NotificationDeliveryAttempt`.

Baseline states:

```text
PENDING
SENT
FAILED
```

Recorded fields include:

```text
notification_id
project_id
idempotency_key
attempt_number
recipient
status
created_at
completed_at
provider_message_id
error_message
```

## 9. Duplicate Suppression

Notification Broker uses an idempotency key.

Default logical key:

```text
<notification_id>:EMAIL:<recipient>
```

If a prior attempt with the same key is already `SENT`, another provider call is suppressed.

SMTP itself does not provide universal exactly-once delivery. A process failure after the remote server accepts a message but before the local `SENT` record is persisted can still produce a duplicate on retry.

Therefore the Phase 3 guarantee is best-effort duplicate suppression, not distributed exactly-once delivery.

## 10. Persistence

The SQLite baseline persists:

- HumanActionRequest records;
- NotificationEvent records;
- NotificationDeliveryAttempt records;
- project operational transitions.

The persistence interface remains backend-neutral.

## 11. Validation

GitHub Actions Phase 3 validation uses Python 3.13 and runs the full pytest suite.

Validated behavior includes:

- project enters `WAITING_FOR_OWNER` for a blocking action;
- verification resumes the affected project;
- unrelated project remains `ACTIVE`;
- notification policy selects immediate owner events;
- duplicate delivery with the same idempotency key is suppressed;
- SMTP relay adapter constructs and sends the structured email through a mocked transport;
- Phase 1 and Phase 2 regression tests continue to pass.

Current automated validation result:

```text
16 passed
```

## 12. Live Delivery Boundary

The code path and SMTP relay adapter are implemented and tested.

A live mailbox delivery test requires project-specific external configuration:

```text
owner recipient address
SMTP relay host
SMTP relay port
STARTTLS policy if required
sender address allowed by the relay
```

Until a real recipient and relay are supplied and one message is confirmed received, Phase 3 remains:

```text
IMPLEMENTATION_COMPLETE
LIVE_DELIVERY_VALIDATION_PENDING
```

No owner address is inferred from repository metadata or other unrelated sources.
