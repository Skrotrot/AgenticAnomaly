import { tool } from "@opencode-ai/plugin"

export default tool({
  description:
    "Publish a SOC investigation report without revoking mTLS credentials.",
  args: {
    report: tool.schema
      .string()
      .describe("Report explaining the SOC investigation outcome"),
  },
  async execute(args) {
    const response = await fetch("http://mtls-website:8444/report", {
      method: "POST",
      body: args.report,
    })

    if (!response.ok) {
      const body = await response.text()
      throw new Error(`Failed to publish SOC report: ${response.status} ${body}`)
    }

    return `SOC report published: ${response.status}`
  },
})
