# VLA REST API Contracts

This document outlines the REST API endpoints for the Vision-Language-Action (VLA) module, detailing their functionality, request formats, and response schemas.

## 1. POST /vla/act

**Description**: Initiates a VLA action based on natural language instructions and visual context.
**Method**: `POST`
**Endpoint**: `/vla/act`
**Request Body**: `application/json`
```json
{
  "instruction": "string",  // Natural language instruction for the robot (e.g., "Pick up the blue object")
  "context_image_rgb": "string" // Base64 encoded RGB image (optional)
  "context_image_depth": "string" // Base64 encoded Depth image (optional)
}
```
**Response Body**: `application/json` (HTTP 200 OK)
```json
{
  "status": "success",
  "action_id": "string", // Unique identifier for the initiated action
  "message": "string" // Confirmation message
}
```
**Error Response**: `application/json` (HTTP 4xx/5xx)
```json
{
  "status": "error",
  "code": "string",    // Error code (e.g., "INVALID_INSTRUCTION", "SAFETY_VIOLATION")
  "message": "string"  // Detailed error message
}
```
**NFRs**:
- p95 latency: <= 50ms (FR-017)
- Throughput: >= 10 actions/sec (FR-018)
