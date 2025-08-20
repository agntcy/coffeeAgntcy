/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import coffeeAgntcyLogo from "@/assets/coffeeAGNTCY_logo.svg"

const Navigation: React.FC = () => {
  return (
    <div className="order-0 box-border flex h-[52px] w-full flex-none flex-grow-0 flex-col items-start self-stretch border-r border-[#DBE0E5] bg-[#F5F8FD] p-0">
      <div className="order-0 box-border flex h-[52px] w-full flex-none flex-grow-0 flex-row items-center justify-between gap-2 self-stretch border-b border-[#D5DFF7] bg-[#EFF3FC] px-4 py-[10px]">
        <div className="order-0 ml-4 flex h-[45px] w-40 flex-none flex-grow-0 flex-row items-center gap-2 p-0 opacity-100">
          <div className="order-0 flex h-[45px] w-40 flex-none flex-grow-0 flex-row items-center gap-1 p-0 opacity-100">
            <div className="order-0 flex h-[42px] w-auto flex-none flex-grow-0 items-center justify-center gap-0.5 opacity-100">
              <img
                src={coffeeAgntcyLogo}
                alt="Coffee AGNTCY Logo"
                className="h-full w-40 object-contain"
              />
            </div>
          </div>
        </div>

        <div className="order-3 flex flex-none flex-grow-0 flex-row items-center justify-end gap-2 p-0">
          <span
            className="order-0 flex-grow-1 flex-none text-right font-inter text-sm font-normal leading-5 text-[#1D69CC]"
            style={{ letterSpacing: "0.25px" }}
          >
            Version 0.4
          </span>
        </div>
      </div>
    </div>
  )
}

export default Navigation
