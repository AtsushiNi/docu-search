import React, { useState, useEffect } from 'react';
import { Table, Card, Statistic, Row, Col, Tag, Button, Space, Select, message } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import type { RQJob, QueueStats } from '../types';
import { getJobList, getQueueStats } from '../services/api';

const { Option } = Select;

const JobsPage: React.FC = () => {
  const [jobs, setJobs] = useState<RQJob[]>([]);
  const [stats, setStats] = useState<QueueStats>({});
  const [loading, setLoading] = useState(false);
  const [selectedQueue, setSelectedQueue] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');

  const statusColors: Record<string, string> = {
    queued: 'blue',
    started: 'orange',
    finished: 'green',
    failed: 'red',
    deferred: 'purple',
    scheduled: 'cyan',
    unknown: 'default'
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const [jobsData, statsData] = await Promise.all([
        getJobList(selectedQueue || undefined, selectedStatus || undefined),
        getQueueStats()
      ]);
      setJobs(jobsData);
      setStats(statsData);
    } catch (error) {
      console.error('Error fetching job data:', error);
      message.error('ジョブデータの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedQueue, selectedStatus]);

  const formatDateTime = (date: string | null) => {
    if (!date) return '-';
    const d = new Date(date);
    // 日本時間 (UTC+9) に変換
    const jstOffset = 9 * 60; // 分単位でのオフセット
    const jstTime = new Date(d.getTime() + jstOffset * 60 * 1000);
    return `${jstTime.getMonth() + 1}/${jstTime.getDate()} ${jstTime.getHours().toString().padStart(2, '0')}:${jstTime.getMinutes().toString().padStart(2, '0')}`;
  };

  const columns = [
    {
      title: 'キュー',
      dataIndex: 'queue',
      key: 'queue',
      width: 100,
      render: (queue: string) => <Tag color="blue">{queue}</Tag>
    },
    {
      title: 'ステータス',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status: string) => {
        const statusTexts: Record<string, string> = {
          queued: '待機中',
          started: '実行中',
          finished: '完了',
          failed: '失敗',
          deferred: '延期',
          scheduled: '予定',
          unknown: '不明'
        };
        return (
          <Tag color={statusColors[status] || 'default'}>
            {statusTexts[status] || status}
          </Tag>
        );
      }
    },
    {
      title: 'ファイルパス',
      dataIndex: 'args',
      key: 'args',
      width: 120,
      render: (args: unknown[]) => (
        <span style={{ fontFamily: 'monospace', fontSize: '11px' }}>
          {args && args.length > 0 ? String(args[0]) : '-'}
        </span>
      )
    },
    {
      title: '作成日時',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 100,
      render: formatDateTime
    },
    {
      title: '開始日時',
      dataIndex: 'started_at',
      key: 'started_at',
      width: 120,
      render: formatDateTime
    },
    {
      title: '終了日時',
      dataIndex: 'ended_at',
      key: 'ended_at',
      width: 120,
      render: formatDateTime
    }
  ];

  const getTotalJobs = () => {
    return Object.values(stats).reduce((total, queueStats) => 
      total + queueStats.queued_jobs + queueStats.started_jobs + queueStats.failed_jobs + queueStats.successful_jobs, 0
    );
  };

  const getQueuedJobs = () => {
    return Object.values(stats).reduce((total, queueStats) => 
      total + queueStats.queued_jobs, 0
    );
  };

  const getStartedJobs = () => {
    return Object.values(stats).reduce((total, queueStats) => 
      total + queueStats.started_jobs, 0
    );
  }

  const getSuccessfulJobs = () => {
    return Object.values(stats).reduce((total, queueStats) => 
      total + queueStats.successful_jobs, 0
    );
  };

  const getFailedJobs = () => {
    return Object.values(stats).reduce((total, queueStats) => 
      total + queueStats.failed_jobs, 0
    );
  };

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={5}>
          <Card>
            <Statistic
              title="総ジョブ数"
              value={getTotalJobs()}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={3}></Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="実行待ちジョブ"
              value={getQueuedJobs()}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="実行中ジョブ"
              value={getStartedJobs()}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="成功ジョブ"
              value={getSuccessfulJobs()}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="失敗ジョブ数"
              value={getFailedJobs()}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      <Card 
        title="ジョブ一覧"
        extra={
          <Space>
            <Select
              placeholder="キューでフィルター"
              value={selectedQueue || undefined}
              onChange={setSelectedQueue}
              style={{ width: 120 }}
              allowClear
            >
              <Option value="">すべて</Option>
              <Option value="default">default</Option>
              <Option value="import_file">import_file</Option>
              <Option value="explore_folder">explore_folder</Option>
            </Select>
            <Select
              placeholder="ステータスでフィルター"
              value={selectedStatus || undefined}
              onChange={setSelectedStatus}
              style={{ width: 120 }}
              allowClear
            >
              <Option value="">すべて</Option>
              <Option value="queued">実行待ち</Option>
              <Option value="started">実行中</Option>
              <Option value="finished">成功</Option>
              <Option value="failed">失敗</Option>
            </Select>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={fetchData}
              loading={loading}
            >
              更新
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={jobs}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1000 }}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} / ${total} 件`
          }}
        />
      </Card>
    </div>
  );
};

export default JobsPage;
