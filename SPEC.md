# InsightOut Product Spec

This document defines the product behavior of InsightOut. It describes what the product does, what users can ask it, how it responds, and the constraints it operates under. It is intentionally written as a behavior specification, not as an implementation plan or engineering checklist.

## Purpose

InsightOut is a conversational ecommerce analytics assistant. It helps users ask natural-language questions about ecommerce performance and receive grounded answers based on ecommerce data.

The product is designed for fast exploratory analysis, not for complete BI tooling. A user can ask a question, receive a concise analytical answer, and continue the investigation with relevant follow-up questions.

## Primary user outcomes

Users should be able to:

- ask questions about ecommerce metrics in plain language
- get direct answers backed by the underlying dataset
- inspect key numbers and comparisons without manually writing queries
- view useful visual comparisons when the answer benefits from a bar chart
- continue exploring with suggested next questions

## User experience

### Initial state

When the app opens with no active conversation, it presents a set of starter prompts such as common ecommerce questions related to revenue, products, and customer behavior. These prompts help the user begin without needing to formulate a query from scratch.

### Conversation flow

The user types a question into the chat input and submits it. The app then enters a loading state while the assistant processes the request.

During processing, the user sees status text indicating the assistant is working through the question. Once a result is available, the assistant responds in the conversation thread with a direct answer and a small set of follow-up suggestions.

If the user clicks a suggestion, that suggestion is sent as a new question automatically.

### Response format

Assistant responses are written in markdown and can include:

- brief explanatory prose
- exact metric values and comparisons
- markdown tables for precise figures or multi-row comparisons
- vertical bar charts for discrete comparisons and ranking-style insights

The answer should feel like a helpful analytics summary, not a raw dump of data.

## Supported question types

InsightOut is intended for questions about ecommerce analytics, including but not limited to:

- revenue and order value trends
- product-level performance and rankings
- customer counts and acquisition patterns
- conversion-related questions
- changes over time by month or period
- comparisons across segments such as device, traffic source, geography, or product groups
- high-level performance questions that require aggregation and interpretation

The product is strongest when the question is about a measurable ecommerce outcome supported by the data available to it.

## Data scope and expectations

The system works with sample ecommerce analytics data that contains ecommerce events and related dimensions such as dates, products, customer identifiers, acquisition sources, device context, and geography.

This data is used to answer questions about business performance. The assistant should treat the data as the source of truth and should not invent unsupported metrics or claim conclusions that are not supported by the underlying data.

Answers should be grounded in the observed dataset, with a clear distinction between:

- facts extracted from the data
- summaries computed from those facts
- interpretation of the business meaning of those facts

## Response quality standards

Answers should be clear, concise, and decision-oriented. They should highlight the main takeaway first and then support it with the relevant values.

### Good answer characteristics

- directly addresses the user’s question
- includes the relevant metric or comparison
- gives exact values when necessary
- explains what changed or why it matters
- uses a chart only when it helps highlight a comparison or ranking
- includes natural follow-up questions that are relevant to the topic just discussed

### Poor answer characteristics

- vague or generic statements
- unsupported claims
- excessive raw data dumps
- charting when a succinct explanation would be clearer
- single-number answers with no context
- follow-up suggestions unrelated to the answer

## Chart behavior

Charts are allowed only when they improve understanding of a discrete comparison or ranking.

The system supports a single chart style: vertical bar charts.

Charts are appropriate when the user is comparing:

- products by revenue
- categories by performance
- time periods by value
- ranked results with a clear relative comparison

Charts are not appropriate for:

- single-value answers
- noisy or overly long category lists
- broad narrative questions best explained in prose
- complex multi-dimensional analysis that would require a different visualization

When a chart is used, it should emphasize the key insight in the surrounding text, not replace the supporting detail.

## Tables and exact values

When an answer depends on precise figures or when there are several categories or metrics, the assistant should present values in a markdown table. Tables are the preferred format for exact, comparable numbers.

The product should favor a combination of narrative explanation plus exact data where needed, rather than leaving the user to infer numbers from a chart alone.

## Follow-up suggestions

Every successful answer includes 2 to 3 follow-up questions that naturally extend the current discussion.

These suggestions should:

- align with the topic of the last answer
- invite a deeper or adjacent analysis
- feel like a natural progression of the conversation

The suggestions are not generic prompts; they should be relevant to the data and the user’s current analytical thread.

## Error handling and trust constraints

The product should fail gracefully when it cannot answer confidently.

If an analysis cannot be supported by the data, the assistant should not fabricate a response. It should communicate the limitation clearly and give the user a path to a valid next question.

The product is designed to be a trusted analytics interface, so confidence and evidence matter more than completeness at all costs.

## Boundaries of the product

InsightOut is scoped to ecommerce analytics questions and data analysis. It does not function as a general-purpose chat assistant for unrelated topics or unsupported domains.

The product should stay within the following boundaries:

- answer questions about ecommerce performance, customer behavior, and acquisition patterns
- rely on the underlying analytics dataset for evidence
- use read-only analysis behavior
- avoid unsupported or speculative conclusions
- remain focused on business analytics, not ad hoc data manipulation or operational tasks

## Summary

InsightOut is a conversational analytics assistant for ecommerce questions. It helps users ask plain-language questions, receive grounded answers, compare key numbers, and continue exploring with relevant follow-up prompts. Its core value is turning ecommerce data into clear, accurate, decision-supporting insight without requiring the user to manually build queries or dashboards.
