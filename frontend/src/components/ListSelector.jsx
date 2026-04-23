import React, { useState } from 'react';
import '../styles/ListSelector.css';

const LIST_TYPES = [
  { value: 'watching',      label: 'Watching' },
  { value: 'completed',     label: 'Completed' },
  { value: 'plan_to_watch', label: 'Plan to Watch' },
  { value: 'on_hold',       label: 'On Hold' },
];

export default function ListSelector({ currentList, onListChange, disabled = false }) {
  const [isOpen, setIsOpen] = useState(false);

  const currentListObj = LIST_TYPES.find((lt) => lt.value === currentList);

  const handleSelect = (listType) => {
    if (!disabled && onListChange) onListChange(listType);
    setIsOpen(false);
  };

  const handleRemove = () => {
    if (!disabled && onListChange) onListChange(null);
    setIsOpen(false);
  };

  return (
    <div className={`list-selector ${disabled ? 'disabled' : ''}`}>
      <button
        className={`list-selector-button ${currentList ? 'has-list' : ''}`}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
      >
        {currentList && currentListObj ? (
          <span>{currentListObj.label}</span>
        ) : (
          <span className="add-to-list-text">+ Add to List</span>
        )}
        <span className="dropdown-arrow">{isOpen ? '▲' : '▼'}</span>
      </button>

      {isOpen && !disabled && (
        <div className="list-selector-dropdown">
          {LIST_TYPES.map((listType) => (
            <button
              key={listType.value}
              className={`list-option ${currentList === listType.value ? 'selected' : ''}`}
              onClick={() => handleSelect(listType.value)}
            >
              <span>{listType.label}</span>
              {currentList === listType.value && (
                <span className="checkmark">✓</span>
              )}
            </button>
          ))}

          {currentList && (
            <>
              <div className="list-option-divider" />
              <button className="list-option remove-option" onClick={handleRemove}>
                <span>Remove from List</span>
              </button>
            </>
          )}
        </div>
      )}

      {isOpen && !disabled && (
        <div className="list-selector-overlay" onClick={() => setIsOpen(false)} />
      )}
    </div>
  );
}
