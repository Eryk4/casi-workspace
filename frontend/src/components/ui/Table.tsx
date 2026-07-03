import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export type TableColumn<T> = {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  align?: "left" | "center" | "right";
};

type TableProps<T> = {
  columns: Array<TableColumn<T>>;
  data: T[];
  emptyMessage?: string;
  getRowKey: (row: T, index: number) => string;
};

export function Table<T>({ columns, data, emptyMessage = "Brak danych do wyswietlenia.", getRowKey }: TableProps<T>) {
  return (
    <div className="ui-table-wrap">
      <table className="ui-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th className={cn(column.align && `is-${column.align}`)} key={column.key} scope="col">
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length ? (
            data.map((row, index) => (
              <tr key={getRowKey(row, index)}>
                {columns.map((column) => (
                  <td className={cn(column.align && `is-${column.align}`)} key={column.key}>
                    {column.render(row)}
                  </td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td className="ui-table__empty" colSpan={columns.length}>
                {emptyMessage}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
