/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect } from "react"
import { createPortal } from "react-dom"
import { BadgeData } from "./types"

const Spinner: React.FC = () => (
  <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-solid border-node-text-primary border-r-transparent"></div>
)

interface BadgeDetailsModalProps {
  isOpen: boolean
  onClose: () => void
  farmName: string
  position: { x: number; y: number }
}

const BadgeDetailsModal: React.FC<BadgeDetailsModalProps> = ({
  isOpen,
  onClose,
  farmName,
  position,
}) => {
  const [badgeData, setBadgeData] = useState<BadgeData | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isOpen) {
      fetchBadgeDetails()
    }
  }, [isOpen, farmName])

  const fetchBadgeDetails = async () => {
    setLoading(true)
    await new Promise((resolve) => setTimeout(resolve, 500))

    const mockData: BadgeData = {
      context: [
        "https://www.w3.org/ns/credentials/v2",
        "https://www.w3.org/ns/credentials/examples/v2",
      ],
      type: ["BADGE_TYPE_AGENT_BADGE"],
      issuer: "zealous-blackburn-23dj9c1kzu.projects.oryapis.com",
      credentialSubject: {
        id: "ORY-f9521354-aa71-4fa7-a983-952e0e2285f8",
        badge:
          '{"capabilities":{"streaming":true},"defaultInputModes":["text"],"defaultOutputModes":["text"],"description":"An AI agent that returns the yield of coffee beans in pounds for the Vietnam farm.","name":"Vietnam Coffee Farm","preferredTransport":"JSONRPC","protocolVersion":"0.3.0","security":[{"IdentityServiceAuthScheme":["*"]}],"securitySchemes":{"IdentityServiceAuthScheme":{"bearerFormat":"JWT","scheme":"bearer","type":"http"}},"skills":[{"description":"Returns the coffee farm\'s yield in lb.","examples":["What is the yield of the Vietnam coffee farm?","How much coffee does the Vietnam farm produce?","What is the yield of the Vietnam coffee farm in pounds?","How many pounds of coffee does the Vietnam farm produce?"],"id":"get_yield","name":"Get Coffee Yield","tags":["coffee","farm"]}],"supportsAuthenticatedExtendedCard":false,"url":"","version":"1.0.0"}',
      },
      id: "d6a1142f-d39c-4fd1-916f-e4a1606ca372",
      issuanceDate: "2025-11-05T22:01:07Z",
      expirationDate: "",
      credentialSchema: [],
      credentialStatus: [],
      proof: {
        type: "jwt",
        proofPurpose: "",
        proofValue:
          "eyJhbGciOiJSUzI1NiIsImtpZCI6IjEwMTBkZGEwLTRiNmUtNDYzNC04MTUyLWRjNzQ5NDQzYjU5NSJ9.eyJjb250ZXh0IjpbImh0dHBzOi8vd3d3LnczLm9yZy9ucy9jcmVkZW50aWFscy92MiIsImh0dHBzOi8vd3d3LnczLm9yZy9ucy9jcmVkZW50aWFscy9leGFtcGxlcy92MiJdLCJ0eXBlIjpbIkJBREdFX1RZUEVfQUdFTlRfQkFER0UiXSwiaXNzdWVyIjoiemVhbG91cy1ibGFja2J1cm4tMjNkajljMWt6dS5wcm9qZWN0cy5vcnlhcGlzLmNvbSIsImNyZWRlbnRpYWxTdWJqZWN0Ijp7ImlkIjoiT1JZLWY5NTIxMzU0LWFhNzEtNGZhNy1hOTgzLTk1MmUwZTIyODVmOCIsImJhZGdlIjoie1wiY2FwYWJpbGl0aWVzXCI6e1wic3RyZWFtaW5nXCI6dHJ1ZX0sXCJkZWZhdWx0SW5wdXRNb2Rlc1wiOltcInRleHRcIl0sXCJkZWZhdWx0T3V0cHV0TW9kZXNcIjpbXCJ0ZXh0XCJdLFwiZGVzY3JpcHRpb25cIjpcIkFuIEFJIGFnZW50IHRoYXQgcmV0dXJucyB0aGUgeWllbGQgb2YgY29mZmVlIGJlYW5zIGluIHBvdW5kcyBmb3IgdGhlIFZpZXRuYW0gZmFybS5cIixcIm5hbWVcIjpcIlZpZXRuYW0gQ29mZmVlIEZhcm1cIixcInByZWZlcnJlZFRyYW5zcG9ydFwiOlwiSlNPTlJQQ1wiLFwicHJvdG9jb2xWZXJzaW9uXCI6XCIwLjMuMFwiLFwic2VjdXJpdHlcIjpbe1wiSWRlbnRpdHlTZXJ2aWNlQXV0aFNjaGVtZVwiOltcIipcIl19XSxcInNlY3VyaXR5U2NoZW1lc1wiOntcIklkZW50aXR5U2VydmljZUF1dGhTY2hlbWVcIjp7XCJiZWFyZXJGb3JtYXRcIjpcIkpXVFwiLFwic2NoZW1lXCI6XCJiZWFyZXJcIixcInR5cGVcIjpcImh0dHBcIn19LFwic2tpbGxzXCI6W3tcImRlc2NyaXB0aW9uXCI6XCJSZXR1cm5zIHRoZSBjb2ZmZWUgZmFybSdzIHlpZWxkIGluIGxiLlwiLFwiZXhhbXBsZXNcIjpbXCJXaGF0IGlzIHRoZSB5aWVsZCBvZiB0aGUgVmlldG5hbSBjb2ZmZWUgZmFybT9cIixcIkhvdyBtdWNoIGNvZmZlZSBkb2VzIHRoZSBWaWV0bmFtIGZhcm0gcHJvZHVjZT9cIixcIldoYXQgaXMgdGhlIHlpZWxkIG9mIHRoZSBWaWV0bmFtIGNvZmZlZSBmYXJtIGluIHBvdW5kcz9cIixcIkhvdyBtYW55IHBvdW5kcyBvZiBjb2ZmZWUgZG9lcyB0aGUgVmlldG5hbSBmYXJtIHByb2R1Y2U_XCJdLFwiaWRcIjpcImdldF95aWVsZFwiLFwibmFtZVwiOlwiR2V0IENvZmZlZSBZaWVsZFwiLFwidGFnc1wiOltcImNvZmZlZVwiLFwiZmFybVwiXX1dLFwic3VwcG9ydHNBdXRoZW50aWNhdGVkRXh0ZW5kZWRDYXJkXCI6ZmFsc2UsXCJ1cmxcIjpcIlwiLFwidmVyc2lvblwiOlwiMS4wLjBcIn0ifSwiaWQiOiJkNmExMTQyZi1kMzljLTRmZDEtOTE2Zi1lNGExNjA2Y2EzNzIiLCJpc3N1YW5jZURhdGUiOiIyMDI1LTExLTA1VDIyOjAxOjA3WiJ9.pTVR3346jO0aD0H6AnSyR79zm6DZoHexT_pY2zJNmSKAvzfVoeRTMA7c0MRdFJpg-Q4Dv_A5R1b3yw-JjJixKZMyaw374eplhJkc7Gr1KPbDNxDtElw47V-jOgSZaYRBRYQiqKec7SLE5bQD_UrYixepxsTxq8dUrz_hQrTVdgeGBgifyMmfjwYG7GLkZ5y6hkX1Joxll2vCc6AzzYc-emjle9WW3u-QZFAB94U012VfsaHoT4IVEflcD7n0SpWF56zI9eLmlpziweQLumkBhZlF0V75yvO4fYqMX4b9SKrNUiwBw3JYvcn4qMs_gvKvtCl1oEXd46Pki2iC7BzZ_A",
      },
      badge: {
        capabilities: {
          streaming: true,
        },
        defaultInputModes: ["text"],
        defaultOutputModes: ["text"],
        description:
          "An AI agent that returns the yield of coffee beans in pounds for the Vietnam farm.",
        name: "Vietnam Coffee Farm",
        preferredTransport: "JSONRPC",
        protocolVersion: "0.3.0",
        security: [
          {
            IdentityServiceAuthScheme: ["*"],
          },
        ],
        securitySchemes: {
          IdentityServiceAuthScheme: {
            bearerFormat: "JWT",
            scheme: "bearer",
            type: "http",
          },
        },
        skills: [
          {
            description: "Returns the coffee farm's yield in lb.",
            examples: [
              "What is the yield of the Vietnam coffee farm?",
              "How much coffee does the Vietnam farm produce?",
              "What is the yield of the Vietnam coffee farm in pounds?",
              "How many pounds of coffee does the Vietnam farm produce?",
            ],
            id: "get_yield",
            name: "Get Coffee Yield",
            tags: ["coffee", "farm"],
          },
        ],
        supportsAuthenticatedExtendedCard: false,
        url: "",
        version: "1.0.0",
      },
    }

    setBadgeData(mockData)
    setLoading(false)
  }

  if (!isOpen) return null

  const handleModalClick = (e: React.MouseEvent) => {
    e.stopPropagation()
  }

  return createPortal(
    <div className="pointer-events-none fixed inset-0 z-50">
      <div
        className="pointer-events-auto absolute -translate-x-1/2"
        style={{
          left: `${position.x}px`,
          top: `${position.y}px`,
        }}
      >
        <div
          className="relative flex max-h-[36vh] w-[500px] flex-col items-start gap-4 rounded-md bg-node-background p-4 shadow-lg"
          onClick={handleModalClick}
          data-modal-content
        >
          {/* Close button - absolute positioned overlay */}
          <button
            onClick={onClose}
            className="absolute right-2 top-2 z-10 rounded-full bg-gray-700 bg-opacity-50 p-1 text-lg leading-none text-node-text-primary hover:bg-opacity-70"
          >
            ×
          </button>

          {loading ? (
            <div className="flex w-full items-center justify-center py-8">
              <Spinner />
            </div>
          ) : badgeData ? (
            <div className="flex max-h-[26vh] min-h-0 w-full flex-col gap-3 overflow-y-auto">
              <h3 className="mb-3 text-lg font-semibold text-node-text-primary">
                {farmName} Badge Details
              </h3>
              <pre className="overflow-auto whitespace-pre-wrap rounded border bg-gray-500 bg-opacity-20 p-3 font-mono text-xs text-node-text-primary">
                {JSON.stringify(badgeData, null, 2)}
              </pre>
            </div>
          ) : (
            <div className="flex w-full items-center justify-center py-8">
              <div className="text-node-text-primary">No data available</div>
            </div>
          )}
        </div>
      </div>
    </div>,
    document.body,
  )
}

export default BadgeDetailsModal
