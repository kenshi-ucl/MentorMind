import * as React from "react";
import { cn } from "../../lib/utils";
import { ChevronDown } from "lucide-react";

const AccordionContext = React.createContext({});
const AccordionItemContext = React.createContext({});

const Accordion = ({ type = "single", collapsible = false, defaultValue, children, className, ...props }) => {
  const [openItems, setOpenItems] = React.useState(
    defaultValue ? (Array.isArray(defaultValue) ? defaultValue : [defaultValue]) : []
  );

  const toggleItem = (value) => {
    setOpenItems((prev) => {
      if (type === "single") {
        if (prev.includes(value) && collapsible) {
          return [];
        }
        return [value];
      }
      if (prev.includes(value)) {
        return prev.filter((item) => item !== value);
      }
      return [...prev, value];
    });
  };

  return (
    <AccordionContext.Provider value={{ openItems, toggleItem }}>
      <div className={cn("w-full", className)} {...props}>
        {children}
      </div>
    </AccordionContext.Provider>
  );
};

const AccordionItem = React.forwardRef(({ className, value, ...props }, ref) => (
  <AccordionItemContext.Provider value={{ value }}>
    <div
      ref={ref}
      className={cn("border-b border-gray-200 dark:border-gray-800", className)}
      {...props}
    />
  </AccordionItemContext.Provider>
));
AccordionItem.displayName = "AccordionItem";

const AccordionTrigger = React.forwardRef(({ className, children, ...props }, ref) => {
  const { openItems, toggleItem } = React.useContext(AccordionContext);
  const { value } = React.useContext(AccordionItemContext);
  const isOpen = openItems.includes(value);

  return (
    <h3 className="flex">
      <button
        ref={ref}
        className={cn(
          "flex flex-1 items-center justify-between py-4 text-sm font-medium transition-all hover:underline [&[data-state=open]>svg]:rotate-180",
          className
        )}
        onClick={() => toggleItem(value)}
        data-state={isOpen ? "open" : "closed"}
        {...props}
      >
        {children}
        <ChevronDown
          className={cn(
            "h-4 w-4 shrink-0 text-gray-500 transition-transform duration-200 dark:text-gray-400",
            isOpen && "rotate-180"
          )}
        />
      </button>
    </h3>
  );
});
AccordionTrigger.displayName = "AccordionTrigger";

const AccordionContent = React.forwardRef(({ className, children, ...props }, ref) => {
  const { openItems } = React.useContext(AccordionContext);
  const { value } = React.useContext(AccordionItemContext);
  const isOpen = openItems.includes(value);

  if (!isOpen) return null;

  return (
    <div
      ref={ref}
      className={cn("overflow-hidden text-sm", className)}
      {...props}
    >
      <div className="pb-4 pt-0">{children}</div>
    </div>
  );
});
AccordionContent.displayName = "AccordionContent";

export { Accordion, AccordionItem, AccordionTrigger, AccordionContent };
