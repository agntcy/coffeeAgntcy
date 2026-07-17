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

  try {
    const response = await httpFetch(url, {
      ...options,
      endpointLabel,
      headers: {
        Accept: "application/json",
        ...options.headers,
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
