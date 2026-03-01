import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import CaptionPanel from "@/components/CaptionPanel";

vi.mock("@/lib/api", () => ({
  getCaptions: vi.fn(async () => `1
00:00:01,000 --> 00:00:03,000
First caption line

2
00:00:03,000 --> 00:00:05,000
Second caption line`),
  chatWithModuleStream: vi.fn(async () => undefined),
}));

describe("CaptionPanel", () => {
  it("seeks video when caption is clicked", async () => {
    const onSeekTo = vi.fn();
    render(<CaptionPanel moduleId="module-1" currentTime={0} onSeekTo={onSeekTo} />);

    await waitFor(() => {
      expect(screen.getByText("First caption line")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "First caption line" }));
    expect(onSeekTo).toHaveBeenCalledWith(1);
  });
});
