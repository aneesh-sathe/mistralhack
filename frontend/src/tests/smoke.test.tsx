import { render, screen } from "@testing-library/react";

import UploadDropzone from "@/components/UploadDropzone";

describe("UploadDropzone", () => {
  it("renders upload prompt", () => {
    render(<UploadDropzone onUpload={async () => undefined} />);
    expect(screen.getByText(/Upload PDF/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Choose PDF/i })).toBeInTheDocument();
  });
});
