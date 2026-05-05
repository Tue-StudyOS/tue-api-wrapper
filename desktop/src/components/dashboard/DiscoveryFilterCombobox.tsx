import { useEffect, useMemo, useRef, useState } from "react";

import type { CourseDiscoveryFacetOption } from "../../lib/course-discovery-types";

interface DiscoveryFilterComboboxProps {
  label: string;
  options: CourseDiscoveryFacetOption[];
  placeholder: string;
  values: string[];
  onChange: (values: string[]) => void;
}

export function DiscoveryFilterCombobox({
  label,
  options,
  placeholder,
  values,
  onChange
}: DiscoveryFilterComboboxProps) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const rootRef = useRef<HTMLDivElement | null>(null);
  const filteredOptions = useMemo(() => {
    const selected = new Set(values.map((item) => item.toLowerCase()));
    const needle = draft.trim().toLowerCase();
    const matches = needle
      ? options.filter((option) => option.label.toLowerCase().includes(needle) || option.value.toLowerCase().includes(needle))
      : options;
    return matches.filter((option) => !selected.has(option.value.toLowerCase()));
  }, [draft, options, values]);

  useEffect(() => {
    function closeOnOutsideClick(event: PointerEvent) {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    window.addEventListener("pointerdown", closeOnOutsideClick);
    return () => window.removeEventListener("pointerdown", closeOnOutsideClick);
  }, []);

  return (
    <div className="field discovery-combobox-field" ref={rootRef}>
      <span>{label}</span>
      {values.length ? (
        <div className="discovery-filter-chip-list">
          {values.map((item) => (
            <button key={item} onClick={() => onChange(values.filter((value) => value !== item))} type="button">
              <span>{item}</span>
              <strong>x</strong>
            </button>
          ))}
        </div>
      ) : null}
      <div className="discovery-combobox">
        <input
          aria-expanded={open}
          aria-haspopup="listbox"
          onChange={(event) => {
            setDraft(event.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={(event) => {
            if (event.key === "Escape") setOpen(false);
            if (event.key === "Enter" && filteredOptions[0]) {
              event.preventDefault();
              onChange([...values, filteredOptions[0].value]);
              setDraft("");
              setOpen(false);
            }
          }}
          placeholder={placeholder}
          role="combobox"
          value={draft}
        />
        <button
          aria-label={`Show ${label} options`}
          className="discovery-combobox-toggle"
          onClick={() => setOpen((current) => !current)}
          type="button"
        >
          v
        </button>
        {open ? (
          <div className="discovery-combobox-menu" role="listbox">
            {filteredOptions.map((option) => (
              <button
                className="discovery-combobox-option"
                key={option.value}
                onClick={() => {
                  onChange([...values, option.value]);
                  setDraft("");
                  setOpen(false);
                }}
                role="option"
                type="button"
              >
                <strong>{option.label}</strong>
                <span>{option.count}</span>
              </button>
            ))}
            {!filteredOptions.length ? <p className="discovery-combobox-empty">No matching options</p> : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
