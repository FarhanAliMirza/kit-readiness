import { driver } from "./vendor/driver.js/driver.js.mjs";

function step(element, title, description) {
  return { element, popover: { title, description } };
}

const tours = {
  readiness: {
    action: "Check readiness",
    description: "Run a live check of available stock at the assembly location.",
    results: [
      step(".summary", "Read the build capacity",
        "The heading shows how many complete kits you can build on site today. The limiting components set that number."),
      step("#table-wrap", "Find the shortages",
        "Compare required quantities with available on-site stock."),
    ],
  },
  transfer: {
    action: "Plan transfers",
    description: "Check other stock locations for components missing at the assembly location.",
    results: [
      step("#suggested-transfers", "Review suggested moves",
        "Each suggested move lists a component, quantity, and source location. These are drafts for the coordinator to review."),
      step("#table-wrap", "See what is still missing",
        "The After transfers column shows the remaining shortage for each component if all suggested moves go ahead."),
    ],
  },
  purchase: {
    action: "Draft purchase list",
    description: "Account for available transfers and eligible incoming stock before calculating what to buy.",
    results: [
      step("#open-orders", "Check incoming stock",
        "Outstanding stock counts toward the remaining shortage when it is due by the needed-by date at the assembly location."),
      step("#table-wrap", "Read the draft purchase quantities",
        "Suggested purchase shows the balance to buy after transfers and eligible orders. Use these quantities to prepare an order."),
    ],
  },
};

export function startDemo(workflow, runPlan) {
  const tour = tours[workflow];
  const trace = step("#tool-trace", "Inspect the Synapse reads",
    "The trace lists each tool the planner called and how many records it returned.");
  trace.onHighlightStarted = (details) => { details.open = true; };

  const action = step(`button[value="${workflow}"]`, tour.action, tour.description);
  action.disableActiveInteraction = true;
  action.popover.nextBtnText = "Run plan";
  action.popover.onNextClick = async (_element, _step, { driver: demo }) => {
    demo.updatePopover({
      description: "Reading live inventory through Synapse…",
      nextBtnText: "Running…",
      disableButtons: ["next", "previous"],
    });
    const succeeded = await runPlan(workflow);
    if (!demo.isActive()) return;

    if (succeeded) {
      demo.moveNext();
    } else {
      demo.updatePopover({
        description: "The plan could not load. Try again or close the demo to see the planner error.",
        nextBtnText: "Try again",
        disableButtons: [],
      });
    }
  };

  driver({
    animate: !window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    showProgress: true,
    popoverClass: "kit-tour",
    doneBtnText: "Finish",
    closeBtnLabel: "Close demo",
    steps: [
      {
        ...step(".fields", "Review the plan inputs",
          "This demo uses the selected kit, assembly location, quantity, and deadline. You can change these before starting a demo."),
        disableActiveInteraction: true,
      },
      action,
      ...tour.results,
      trace,
    ],
  }).drive();
}
