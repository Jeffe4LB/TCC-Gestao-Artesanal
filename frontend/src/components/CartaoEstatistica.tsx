import { Card, Statistic, Typography } from "antd";

export function CartaoEstatistica({
  title,
  value,
  color,
  subtitle,
}: {
  title: string;
  value: number | string;
  color: string;
  subtitle?: string;
}) {
  return (
    <Card
      style={{
        borderRadius: 16,
        border: "1px solid #f0f0f0",
        borderLeft: `4px solid ${color}`,
        background: "#fafafa",
        boxShadow: "0 4px 12px rgba(0,0,0,0.05)",
        transition: "all 0.25s ease",
      }}
      bodyStyle={{ padding: 24 }} 
      hoverable
    >
      <Typography.Text type="secondary" style={{ fontSize: 13 }}>
        {title}
      </Typography.Text>

      <Statistic
        value={value}
        valueStyle={{
          color,
          fontSize: 28,
          fontWeight: 600,
          marginTop: 4,
        }}
      />

      {subtitle && (
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          {subtitle}
        </Typography.Text>
      )}
    </Card>
  );
}