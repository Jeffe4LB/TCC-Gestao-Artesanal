import { Pagination } from "antd";

const DEFAULT_PAGE_SIZE = 20;

type Props = {
  page: number; 
  totalCount: number;
  pageSize?: number;
  onPageChange: (p: number) => void;
};

export function BarraPaginacao({
  page,
  totalCount,
  pageSize = DEFAULT_PAGE_SIZE,
  onPageChange,
}: Props) {
  return (
    <div style={{ marginTop: 16, display: "flex", justifyContent: "flex-end" }}>
      <Pagination
        current={page}
        total={totalCount}
        pageSize={pageSize}
        onChange={(p) => onPageChange(p)}
        showSizeChanger={false}
        showTotal={(total) => `${total} itens`}
      />
    </div>
  );
}
