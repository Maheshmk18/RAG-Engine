import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Markdown } from "./Markdown";

test("renders citation markers as buttons for known sources", async () => {
  const onCite = vi.fn();
  render(
    <Markdown
      text={"You get **25 days** of leave [1]. Up to 5 days carry over [2]."}
      available={new Set([1])}
      onCite={onCite}
    />,
  );

  const first = screen.getByRole("button", { name: "Show source 1" });
  const second = screen.getByRole("button", { name: "Show source 2" });
  expect(second).toBeDisabled();
  expect(screen.getByText("25 days").tagName).toBe("STRONG");

  await userEvent.click(first);
  expect(onCite).toHaveBeenCalledWith(1);
});

test("leaves text without markers untouched", () => {
  render(<Markdown text="No citations in this sentence." available={new Set()} />);
  expect(screen.queryByRole("button")).not.toBeInTheDocument();
  expect(screen.getByText("No citations in this sentence.")).toBeInTheDocument();
});
