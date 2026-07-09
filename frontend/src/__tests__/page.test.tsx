import { render, screen } from "@testing-library/react";
import Home from "@/app/page";

describe("Home Page", () => {
  it("renders the project name", () => {
    render(<Home />);
    const heading = screen.getByText("SleepMate Agent");
    expect(heading).toBeInTheDocument();
  });

  it("renders the subtitle", () => {
    render(<Home />);
    const subtitle = screen.getByText("AI 助眠助手");
    expect(subtitle).toBeInTheDocument();
  });
});
