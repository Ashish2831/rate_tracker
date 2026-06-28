/** Searchable combobox for provider and rate-type dashboard filters. */

"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";

import {
  filterOptions,
  resolveFilterOption,
} from "@/lib/filterOptions";
import { FilterOption, SearchableFilterProps } from "@/interfaces/filters";
import styles from "@/app/page.module.css";

export function SearchableFilter({ label, allLabel, options, value, onChange }: SearchableFilterProps) {
  const listId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  // Refs avoid blur/focus races when selecting or clearing from mousedown handlers.
  const ignoreBlurRef = useRef(false);
  /** Skip restoring the previous label on focus after clear (parent value may still be stale). */
  const skipFocusRestoreRef = useRef(false);
  /** Clear button unmounts on the same mousedown; suppress the outside-click close for that event. */
  const suppressOutsideCloseRef = useRef(false);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);

  const selected = options.find((option) => option.value === value);
  const visibleOptions = useMemo(() => {
    const matched = filterOptions(query, options);
    // Prepend “All …” when query is empty or matches the allLabel text.
    if (!query.trim() || allLabel.toLowerCase().includes(query.trim().toLowerCase())) {
      return [{ value: "", label: allLabel }, ...matched];
    }
    return matched;
  }, [allLabel, options, query]);

  useEffect(() => {
    if (!open) return;
    setActiveIndex(0);
  }, [open, query]);

  useEffect(() => {
    // Close dropdown when clicking outside the combobox root.
    function handlePointerDown(event: MouseEvent) {
      if (suppressOutsideCloseRef.current) {
        suppressOutsideCloseRef.current = false;
        return;
      }
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, []);

  function commitQuery(nextQuery: string) {
    // Empty input clears the filter; partial text reverts to the last valid selection.
    if (!nextQuery.trim()) {
      onChange("");
      setQuery("");
      return;
    }
    const resolved = resolveFilterOption(nextQuery, options);
    if (resolved) {
      onChange(resolved.value);
      setQuery("");
      return;
    }
    setQuery(selected?.label ?? "");
  }

  function clearFilter() {
    suppressOutsideCloseRef.current = true;
    ignoreBlurRef.current = true;
    skipFocusRestoreRef.current = true;
    onChange("");
    setQuery("");
    setOpen(true);
    inputRef.current?.focus();
  }

  function selectOption(option: FilterOption) {
    // Blur runs after mousedown; ignore it so commitQuery does not undo the selection.
    ignoreBlurRef.current = true;
    onChange(option.value);
    setQuery("");
    setOpen(false);
    inputRef.current?.blur();
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (!open && (event.key === "ArrowDown" || event.key === "ArrowUp")) {
      setOpen(true);
      return;
    }

    if (event.key === "Escape") {
      setOpen(false);
      setQuery("");
      inputRef.current?.blur();
      return;
    }

    if (!open || visibleOptions.length === 0) return;

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((index) => (index + 1) % visibleOptions.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex(
        (index) => (index - 1 + visibleOptions.length) % visibleOptions.length,
      );
    } else if (event.key === "Enter") {
      event.preventDefault();
      selectOption(visibleOptions[activeIndex] ?? visibleOptions[0]);
    }
  }

  // Show search text while open; collapsed input shows the selected label.
  const displayValue = open ? query : (selected?.label ?? "");

  return (
    <div className={styles.toolbarLabel} ref={rootRef}>
      <span id={`${listId}-label`}>{label}</span>
      <div className={styles.combobox}>
        <input
          ref={inputRef}
          className={styles.comboboxInput}
          type="text"
          role="combobox"
          aria-expanded={open}
          aria-controls={listId}
          aria-labelledby={`${listId}-label`}
          aria-autocomplete="list"
          aria-activedescendant={
            open && visibleOptions[activeIndex]
              ? `${listId}-option-${activeIndex}`
              : undefined
          }
          placeholder={allLabel}
          value={displayValue}
          onFocus={() => {
            setOpen(true);
            if (skipFocusRestoreRef.current) {
              skipFocusRestoreRef.current = false;
              setQuery("");
              return;
            }
            setQuery(value ? (selected?.label ?? "") : "");
          }}
          onBlur={() => {
            if (ignoreBlurRef.current) {
              ignoreBlurRef.current = false;
              return;
            }
            commitQuery(query);
            setOpen(false);
          }}
          onChange={(event) => {
            setQuery(event.target.value);
            setOpen(true);
          }}
          onKeyDown={handleKeyDown}
        />
        {value ? (
          <button
            type="button"
            className={styles.comboboxClear}
            aria-label={`Clear ${label.toLowerCase()} filter`}
            onMouseDown={(event) => {
              // preventDefault: keep input focused; stopPropagation: clear button unmounts this tick.
              event.preventDefault();
              event.stopPropagation();
              clearFilter();
            }}
          >
            ×
          </button>
        ) : null}
        {open && visibleOptions.length > 0 ? (
          <ul className={styles.comboboxList} id={listId} role="listbox">
            {visibleOptions.map((option, index) => (
              <li
                key={option.value || "__all__"}
                id={`${listId}-option-${index}`}
                role="option"
                aria-selected={option.value === value}
                className={
                  index === activeIndex
                    ? `${styles.comboboxOption} ${styles.comboboxOptionActive}`
                    : styles.comboboxOption
                }
                onMouseDown={(event) => {
                  // Select on mousedown (before blur) and keep focus from leaving the input.
                  event.preventDefault();
                  selectOption(option);
                }}
                onMouseEnter={() => setActiveIndex(index)}
              >
                {option.label}
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </div>
  );
}
