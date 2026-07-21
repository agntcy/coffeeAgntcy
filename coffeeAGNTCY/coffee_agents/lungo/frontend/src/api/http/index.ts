/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

export { HttpError, isHttpError, type HttpErrorOptions } from "./types.ts"
export {
  parseHttpError,
  parseHttpErrorFromResponse,
  type ParseHttpErrorOptions,
} from "./parseHttpError.ts"
export { stripHtml } from "./stripHtml.ts"
export { httpFetch, type HttpFetchOptions } from "./httpClient.ts"
export { fetchJson } from "./fetchJson.ts"
export {
  fetchNdjsonStream,
  type FetchNdjsonStreamOptions,
  type NdjsonSplitMode,
} from "./fetchNdjsonStream.ts"
export {
  ndjsonStreamUserMessage,
  asHttpError,
  type NdjsonStreamUserMessageVariant,
} from "./ndjsonStreamUserMessage.ts"
export {
  consumeJsonObjectsFromBuffer,
  consumeNdjsonLines,
} from "./ndjsonParsing.ts"
export {
  fetchSse,
  type FetchSseClose,
  type FetchSseOptions,
} from "./fetchSse.ts"
export {
  parseSseDataLine,
  parseSseFrameLines,
  splitSseFrames,
} from "./sseParsing.ts"
