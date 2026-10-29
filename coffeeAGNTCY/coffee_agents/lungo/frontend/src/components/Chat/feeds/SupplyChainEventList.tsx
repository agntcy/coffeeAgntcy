/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Renders the Supply Chain Commitment stream: the negotiation messages, the
 * commitment record and the checker's verdict.
 **/

import { useState } from "react"
import { Box, Icons, Stack, Typography } from "@open-ui-kit/core"
import type { Theme } from "@mui/material/styles"

import {
  isVisibleSupplyChainMessage,
  supplyChainAddressees,
  supplyChainPartyLabel,
  type SupplyChainMessageEvent,
  type SupplyChainRecord,
  type SupplyChainStreamEvent,
  type SupplyChainVerdict,
} from "@/stores/supplyChainEvents"
import {
  describeSupplyChainStatus,
  formatSupplyChainTimestamp,
  supplyChainSenderName,
} from "./supplyChainFeedText"
import { successIconColorSx } from "@/utils/successIconColor"

const LONG_BODY_CHARS = 360

const wrapSx = { overflowWrap: "break-word", wordBreak: "break-word" } as const

function CollapsibleBody({ text }: { text: string }) {
  const [open, setOpen] = useState(false)
  const isLong = text.length > LONG_BODY_CHARS
  const shown = !isLong || open ? text : `${text.slice(0, LONG_BODY_CHARS)}...`
  return (
    <>
      <Typography
        component="span"
        variant="body1"
        sx={{ whiteSpace: "pre-wrap", ...wrapSx }}
      >
        &quot;{shown}&quot;
      </Typography>
      {isLong ? (
        <Box
          component="button"
          type="button"
          onClick={() => setOpen((v) => !v)}
          sx={{
            ml: 1,
            p: 0,
            border: 0,
            background: "none",
            color: "inherit",
            textDecoration: "underline",
            cursor: "pointer",
            font: "inherit",
          }}
        >
          {open ? "Show less" : "Show more"}
        </Box>
      ) : null}
    </>
  )
}

export function SupplyChainMessageLine({
  event,
}: {
  event: SupplyChainMessageEvent
}) {
  return (
    <Stack
      direction="row"
      alignItems="flex-start"
      spacing={0.5}
      sx={{ width: "100%" }}
      data-testid="supply-chain-message"
    >
      <Box sx={{ mt: 0.5, display: "flex", alignItems: "center" }}>
        <Icons.CheckCircleFilled
          sx={(theme) => successIconColorSx(theme)}
          aria-hidden
        />
      </Box>
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Typography variant="body1" component="div" sx={wrapSx}>
          <Typography component="span" variant="body1">
            {supplyChainSenderName(event.from)}
          </Typography>{" "}
          &rarr;{" "}
          <Typography component="span" variant="body1">
            {supplyChainAddressees(event.to)}
          </Typography>
          : <CollapsibleBody text={event.body} />
        </Typography>
      </Box>
    </Stack>
  )
}

function SupplyChainStatusLine({ text }: { text: string }) {
  return (
    <Typography
      variant="body2"
      component="div"
      sx={{ opacity: 0.8, fontStyle: "italic", ...wrapSx }}
      data-testid="supply-chain-status"
    >
      {text}
    </Typography>
  )
}

const cardSx = (theme: Theme) => ({
  width: "100%",
  border: `1px solid ${theme.palette.divider}`,
  borderRadius: 1,
  p: 2,
})

const planConfirmations = (record: SupplyChainRecord) =>
  record.confirmations.filter(
    (c) =>
      record.plan_version != null && c.plan_version === record.plan_version,
  )

export function SupplyChainRecordCard({
  record,
}: {
  record: SupplyChainRecord
}) {
  const confirmations = planConfirmations(record)
  return (
    <Stack spacing={1} sx={cardSx} data-testid="supply-chain-record">
      <Typography variant="subtitle1" component="div">
        Commitment record
      </Typography>
      <Typography variant="body2" component="div" sx={wrapSx}>
        Status: <strong>{record.status}</strong>
        {record.reason ? ` (${record.reason})` : ""}
        {record.plan_version != null
          ? `, plan version ${record.plan_version}`
          : ""}
      </Typography>
      {record.lots.map((lot) => (
        <Typography
          key={lot.supplier}
          variant="body2"
          component="div"
          sx={wrapSx}
        >
          {supplyChainPartyLabel(lot.supplier)}: {lot.tonnes} t
          {lot.transport_option ? `, ${lot.transport_option}` : ""}
          {lot.claimed_arrival_at
            ? `, arrival claimed ${formatSupplyChainTimestamp(lot.claimed_arrival_at)}`
            : ""}
        </Typography>
      ))}
      {record.destination || record.arrival_deadline ? (
        <Typography variant="body2" component="div" sx={wrapSx}>
          {record.destination ? `Destination: ${record.destination}. ` : ""}
          {record.arrival_deadline
            ? `Deadline: ${formatSupplyChainTimestamp(record.arrival_deadline)}.`
            : ""}
        </Typography>
      ) : null}
      {record.total_cost_usd != null ? (
        <Typography variant="body2" component="div">
          Total transport cost: ${record.total_cost_usd.toLocaleString("en-US")}
        </Typography>
      ) : null}
      {confirmations.length > 0 ? (
        <Typography variant="body2" component="div" sx={wrapSx}>
          Confirmations:{" "}
          {confirmations
            .map((c) => `${supplyChainPartyLabel(c.party)} ${c.decision}`)
            .join(", ")}
        </Typography>
      ) : null}
    </Stack>
  )
}

const VERDICT_TITLES: Record<SupplyChainVerdict["verdict"], string> = {
  PASS: "PASS",
  FAIL: "FAIL",
  INVALID: "INVALID",
}

export function SupplyChainVerdictCard({
  verdict,
}: {
  verdict: SupplyChainVerdict
}) {
  const failed = verdict.verdict === "FAIL"
  return (
    <Stack
      spacing={1}
      sx={(theme) => ({
        ...cardSx(theme),
        borderColor:
          verdict.verdict === "PASS"
            ? theme.palette.success.main
            : failed
              ? theme.palette.error.main
              : theme.palette.divider,
      })}
      data-testid="supply-chain-verdict"
    >
      <Stack direction="row" alignItems="center" spacing={1}>
        <Typography variant="subtitle1" component="div">
          Checker verdict: {VERDICT_TITLES[verdict.verdict]}
        </Typography>
        {verdict.silent ? (
          <Box
            component="span"
            data-testid="supply-chain-silent-badge"
            sx={(theme) => ({
              px: 1,
              py: 0.25,
              borderRadius: 1,
              fontSize: "0.75rem",
              fontWeight: 600,
              color: theme.palette.error.contrastText,
              backgroundColor: theme.palette.error.main,
            })}
          >
            Silent failure
          </Box>
        ) : null}
      </Stack>
      {verdict.silent ? (
        <Typography variant="body2" component="div" sx={wrapSx}>
          All five parties confirmed the plan, and nobody flagged the problem.
        </Typography>
      ) : null}
      {verdict.verdict === "PASS" ? (
        <Typography variant="body2" component="div">
          The committed plan holds up against the scenario facts.
        </Typography>
      ) : null}
      {verdict.verdict === "INVALID" ? (
        <Typography variant="body2" component="div">
          The run ended by an outage and could not be graded.
        </Typography>
      ) : null}
      {verdict.codes.length > 0 ? (
        <Typography variant="body2" component="div" sx={wrapSx}>
          Failure codes: {verdict.codes.join(", ")}
        </Typography>
      ) : null}
      {verdict.details.map((detail, index) => (
        <Typography
          key={`${index}-${detail}`}
          variant="body2"
          component="div"
          sx={wrapSx}
        >
          {detail}
        </Typography>
      ))}
    </Stack>
  )
}

export interface SupplyChainEventListProps {
  events: readonly SupplyChainStreamEvent[]
}

export function SupplyChainEventList({ events }: SupplyChainEventListProps) {
  return (
    <>
      {events.map((event, index) => {
        switch (event.type) {
          case "message":
            return isVisibleSupplyChainMessage(event) ? (
              <SupplyChainMessageLine key={`m-${event.seq}`} event={event} />
            ) : null
          case "status": {
            const text = describeSupplyChainStatus(event)
            return text ? (
              <SupplyChainStatusLine key={`s-${index}`} text={text} />
            ) : null
          }
          case "record":
            return (
              <SupplyChainRecordCard key={`r-${index}`} record={event.record} />
            )
          case "verdict":
            return (
              <SupplyChainVerdictCard
                key={`v-${index}`}
                verdict={event.verdict}
              />
            )
        }
      })}
    </>
  )
}
