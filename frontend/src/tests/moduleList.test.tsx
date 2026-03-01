import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";

import ModuleList from "@/components/ModuleList";
import { ModuleItem } from "@/lib/types";

function moduleFixture(overrides: Partial<ModuleItem> = {}): ModuleItem {
  return {
    id: "module-1",
    document_id: "doc-1",
    title: "Kinematics",
    summary: "Motion basics",
    prerequisites: [],
    chunk_refs: [],
    status: "READY",
    created_at: "2026-03-01T00:00:00.000Z",
    updated_at: "2026-03-01T00:00:00.000Z",
    ...overrides,
  };
}

describe("ModuleList", () => {
  it("calls delete handler when delete is clicked", () => {
    const onDelete = vi.fn();
    const module = moduleFixture();

    render(<ModuleList modules={[module]} onDeleteModule={onDelete} />);

    fireEvent.click(screen.getByRole("button", { name: /Delete/i }));
    expect(onDelete).toHaveBeenCalledWith(module);
  });

  it("disables delete for generating modules", () => {
    render(<ModuleList modules={[moduleFixture({ status: "GENERATING" })]} onDeleteModule={vi.fn()} />);
    expect(screen.getByRole("button", { name: /Delete/i })).toBeDisabled();
  });
});
