import { tool } from "@opencode-ai/plugin"

export default tool({
  description:
    "Revoke mTLS credentials. Requires a report explaining why the credential should be revoked.",
  args: {
    report: tool.schema
      .string()
      .describe("Report explaining why the mTLS credential should be revoked"),
  },
  async execute(args) {
    const response = await fetch("http://mtls-website:8444/revoke", {
      method: "POST",
      body: args.report,
    })

    if (!response.ok) {
      const body = await response.text()
      throw new Error(`Failed to revoke mTLS credential: ${response.status} ${body}`)
    }

    return `Revocation request submitted: ${response.status}`
  },
})
