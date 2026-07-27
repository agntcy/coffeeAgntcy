/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { httpFetch, type HttpFetchOptions } from "./httpClient.ts"
import { parseHttpError } from "./parseHttpError.ts"

export async function fetchJson<T>(
  url: string,
  options: HttpFetchOptions = {},
): Promise<T> {
  const endpointLabel = options.endpointLabel ?? url
  const { headers, body, ...rest } = options

  try {
    const response = await httpFetch(url, {
      ...rest,
      body,
      endpointLabel,
      headers: {
        Accept: "application/json",
        ...(body != null ? { "Content-Type": "application/json" } : {}),
        ...headers,
      },
    })

    try {
      return (await response.json()) as T
    } catch (error) {
      throw parseHttpError(error, { endpointLabel })
    }
  } catch (error) {
    throw parseHttpError(error, { endpointLabel })
  }
}
